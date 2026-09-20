using System.Collections.Generic;
using Common;
using Phys.Fire;
using Phys.Pixels;
using Phys.Terrain;
using UnityEngine;
using CrackerService = Cracker.Cracker;

namespace Phys.Explosions
{
    /// <summary>
    /// One bang, everything it does. Call <see cref="Detonate"/> from wherever the thing went
    /// off — a fused barrel, a shell landing, a scripted event — and hand it an
    /// <see cref="ExplosionProfile"/>.
    ///
    /// The work is done in one overlap query and then split by what each result is: a
    /// <see cref="Damageable"/> takes damage, a <see cref="Rigidbody2D"/> takes a shove, and a
    /// pixel sprite loses the pixels inside the carve radius — through the same
    /// <see cref="PixelSpriteRegistry"/> mirror the eraser and the fire write to, so the hole a
    /// blast leaves is the same kind of hole everything else in the game leaves. Ignition goes
    /// through <see cref="FireSystem"/> for the same reason: the fire a blast starts is the
    /// normal fire, spreading and eating pixels like any other.
    ///
    /// Everything is measured from the blast point outward and faded by
    /// <see cref="ExplosionProfile.Attenuate"/>, so one figure — distance — decides damage,
    /// push and shake together and they cannot disagree about how close something was.
    /// </summary>
    public static class Explosion
    {
        // One blast at a time, so these are shared rather than allocated per detonation.
        private static readonly Collider2D[] Hits = new Collider2D[256];
        private static readonly Dictionary<Damageable, Contact> Victims = new();
        private static readonly Dictionary<Rigidbody2D, Contact> Pushed = new();
        private static readonly Dictionary<GameObject, Contact> Carved = new();
        private static readonly List<Explosive> Caught = new();
        private static readonly List<RaycastHit2D> Line = new();

        private readonly struct Contact
        {
            public readonly Vector2 Point;
            public readonly float Falloff;   // 1 in the core, 0 at the rim

            public Contact(Vector2 point, float falloff)
            {
                Point = point;
                Falloff = falloff;
            }
        }

        /// <summary>
        /// Set one off at <paramref name="center"/>.
        /// </summary>
        /// <param name="source">What to blame for the damage, and — when
        /// <see cref="ExplosionProfile.hurtsOwner"/> is off — what to spare. Its whole hierarchy
        /// is spared, so a rocket does not shoot the launcher off its owner's arm.</param>
        public static void Detonate(Vector2 center, ExplosionProfile p, GameObject source = null)
        {
            if (p == null || p.radius <= 0f) return;

            Gather(center, p, source);
            Damage(center, p, source);
            Push(center, p);
            Carve(center, p);
            Ignite(center, p);
            Flames(center, p);
            Sparks(center, p);
            Shake(center, p);
            Chain(center, p);

            Victims.Clear();
            Pushed.Clear();
            Carved.Clear();
            Caught.Clear();
        }

        /// <summary>Convenience for the common case of a shared profile asset.</summary>
        public static void Detonate(Vector2 center, ExplosionConfig config, GameObject source = null)
        {
            if (config) Detonate(center, config.profile, source);
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Who is in it
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// One overlap query, sorted into the three things a blast can do to something. A body
        /// is measured at the point of it nearest the blast rather than at its origin: a wall
        /// two metres wide is hit where it faces the bomb, not at its middle.
        /// </summary>
        private static void Gather(Vector2 center, ExplosionProfile p, GameObject source)
        {
            var filter = new ContactFilter2D
            {
                useTriggers = false,
                useLayerMask = true,
                layerMask = p.affects,
            };

            // The margin is the pixel tools' own: a carved sprite's collider is retraced a frame
            // behind its pixels, so a query cut to the exact radius can miss the thing it is
            // standing on. Falloff is still measured from the real distance.
            float reach = Mathf.Max(p.radius, p.carveRadius) + PixelSpriteRegistry.QueryMargin;
            int count = Physics2D.OverlapCircle(center, reach, filter, Hits);
            Transform owner = (!p.hurtsOwner && source) ? source.transform.root : null;

            for (int i = 0; i < count; i++)
            {
                var col = Hits[i];
                if (!col) continue;

                var go = col.gameObject;
                if (owner && go.transform.IsChildOf(owner)) continue;

                Vector2 point = col.ClosestPoint(center);
                float dist = Vector2.Distance(point, center);

                // dist is to the nearest point of the collider, so this is exactly "the carve
                // circle reaches this object" — and it is asked first, because something too far
                // out to be hurt can still be standing inside the hole.
                if (p.carveRadius > 0f && dist <= p.carveRadius + PixelSpriteRegistry.QueryMargin)
                    Keep(Carved, go, point, 1f);

                float f = p.Attenuate(dist);
                if (f <= 0f) continue;

                if (dist > p.innerRadius) f *= Cover(center, point, col, p);
                if (f <= 0f) continue;

                var victim = col.GetComponentInParent<Damageable>();
                if (victim && !victim.IsDead) Keep(Victims, victim, point, f);

                var rb = col.attachedRigidbody;
                if (rb && rb.bodyType == RigidbodyType2D.Dynamic) Keep(Pushed, rb, point, f);
            }
        }

        /// <summary>Nearest contact wins: several colliders on one body is one target.</summary>
        private static void Keep<T>(Dictionary<T, Contact> into, T key, Vector2 point, float f)
        {
            if (into.TryGetValue(key, out var had) && had.Falloff >= f) return;
            into[key] = new Contact(point, f);
        }

        /// <summary>
        /// What gets through to a target behind something. The line is drawn to the collider's
        /// own surface, so the target never shadows itself, and only geometry in
        /// <see cref="ExplosionProfile.blockedBy"/> counts — a blast that could be stopped by a
        /// crate is a blast that stops behaving like a blast.
        /// </summary>
        private static float Cover(Vector2 center, Vector2 point, Collider2D target, ExplosionProfile p)
        {
            if (p.blockedBy.value == 0) return 1f;

            Vector2 to = point - center;
            float dist = to.magnitude;
            if (dist <= 0.01f) return 1f;

            var filter = new ContactFilter2D
            {
                useTriggers = false,
                useLayerMask = true,
                layerMask = p.blockedBy,
            };

            Line.Clear();
            Physics2D.Raycast(center, to / dist, filter, Line, dist - 0.01f);

            var root = target.transform.root;
            foreach (var hit in Line)
                if (hit.collider && !hit.collider.transform.IsChildOf(root))
                    return p.coverLeak;

            return 1f;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // What it does to them
        // ─────────────────────────────────────────────────────────────────────────

        private static void Damage(Vector2 center, ExplosionProfile p, GameObject source)
        {
            if (p.damage <= 0f) return;

            foreach (var pair in Victims)
            {
                var victim = pair.Key;
                if (!victim || victim.IsDead) continue;

                float amount = p.damage * pair.Value.Falloff;
                if (amount < p.minDamage) continue;

                Vector2 dir = Away(center, pair.Value.Point);
                victim.ApplyDamage(new DamageInfo(
                    amount, DamageType.Explosion, pair.Value.Point, dir,
                    dir * (p.force * pair.Value.Falloff * p.corpseKick), source));
            }
        }

        private static void Push(Vector2 center, ExplosionProfile p)
        {
            if (p.force <= 0f) return;

            foreach (var pair in Pushed)
            {
                var rb = pair.Key;
                if (!rb) continue;

                var c = pair.Value;
                Vector2 dir = Away(center, c.Point);
                dir = (dir + Vector2.up * p.upwardBias).normalized;

                // Impulse is momentum, so the same figure barely nudges a boulder and launches
                // a pebble. ignoreMass scales it by mass instead, which turns the number into a
                // change in speed and makes a blast throw a crowd of mixed junk evenly.
                float impulse = p.force * c.Falloff * (p.ignoreMass ? rb.mass : 1f);
                rb.AddForceAtPosition(dir * impulse, c.Point, ForceMode2D.Impulse);

                if (p.spin > 0f)
                    rb.AddTorque(Random.Range(-p.spin, p.spin) * c.Falloff, ForceMode2D.Impulse);
            }
        }

        /// <summary>
        /// Take the level with it, along the same lines the crack tool already draws: standing
        /// terrain loses the bite under the blast and keeps standing, while a loose object small
        /// enough to be swallowed by it comes apart whole. A loose object only clipped by the
        /// edge is bitten rather than shattered — a blast that grazes a long plank should not be
        /// able to destroy all of it.
        /// </summary>
        private static void Carve(Vector2 center, ExplosionProfile p)
        {
            if (p.carveRadius <= 0f || Carved.Count == 0) return;

            bool terrainCut = false;
            float falloff = Mathf.Max(0.25f, p.carveRadius);

            foreach (var pair in Carved)
            {
                var go = pair.Key;
                if (!go) continue;

                // Bedrock is the level's floor and walls in the sense of "the thing that is not
                // allowed to stop existing". Everything else is fair game.
                var body = go.GetComponentInParent<TerrainBody>();
                if (body && body.Bedrock) continue;

                if (PixelSpriteRegistry.Instance.Get(go) == null) continue;

                bool anchored = TerrainBody.IsAnchored(go);
                if (anchored) terrainCut = true;

                if (p.shards <= 0)
                {
                    SpriteEraseService.EraseCircle(go, center, p.carveRadius);
                    continue;
                }

                if (!anchored && Swallowed(go, center, p.carveRadius))
                    CrackerService.Crack(go, p.shards, impactWorld: (Vector3)center,
                                         impactImpulse: p.shardImpulse, impactFalloff: falloff);
                else
                    CrackerService.CrackTerrain(go, center, p.carveRadius, p.shards,
                                                p.shardImpulse, falloff);
            }

            // The hole has to be real this frame: things are being thrown into it right now, and
            // a collider that still has the old shape catches them on nothing.
            PixelSpriteDriver.FinalizeNow();
            if (terrainCut) TerrainSupportSystem.Refresh();
        }

        /// <summary>Is the whole object inside the blast's bite?</summary>
        private static bool Swallowed(GameObject go, Vector2 center, float radius)
        {
            var sr = go.GetComponent<SpriteRenderer>();
            if (!sr) return false;

            var b = sr.bounds;
            return b.extents.magnitude <= radius &&
                   Vector2.Distance(b.center, center) <= radius;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Fire
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Light what it touched. Scattered points rather than one big circle: fire that starts
        /// in a dozen places spreads into a burning room, while one disc of lit pixels reads as
        /// a stain and then goes out at its own edges.
        /// </summary>
        private static void Ignite(Vector2 center, ExplosionProfile p)
        {
            if (!p.ignites || p.igniteRadius <= 0f || p.igniteSpots <= 0) return;

            var fire = FireSystem.Instance;
            for (int i = 0; i < p.igniteSpots; i++)
            {
                // Square-rooted so the spots spread evenly over the area instead of crowding
                // into the middle.
                Vector2 spot = center + Random.insideUnitCircle.normalized *
                               (Mathf.Sqrt(Random.value) * p.igniteRadius);
                fire.IgniteAt(spot, p.igniteBrush);
            }
        }

        /// <summary>
        /// The fireball itself: ordinary flame cells, thrown outward and left to do what flames
        /// do. They rise, drift, light what they touch and die on their own, so the blast fades
        /// the way a fire fades rather than on a timer.
        /// </summary>
        private static void Flames(Vector2 center, ExplosionProfile p)
        {
            var field = FlameField.Instance;
            float reach = Mathf.Max(p.igniteRadius, p.radius * 0.6f);

            for (int i = 0; i < p.fireball; i++)
            {
                Vector2 at = center + Random.insideUnitCircle * reach;
                if (!field.Emit(at, p.fireHeat)) break;   // the field is full; the rest would be lost
            }

            for (int i = 0; i < p.smoke; i++)
            {
                Vector2 at = center + Random.insideUnitCircle * (reach * 0.8f);
                if (!field.EmitSmoke(at)) break;
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // Feel
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Flash, ring and debris — see <see cref="ExplosionBurst"/>.</summary>
        private static void Sparks(Vector2 center, ExplosionProfile p) =>
            ExplosionBurst.Spawn(center, p);

        private static void Shake(Vector2 center, ExplosionProfile p)
        {
            var cam = Siege.CameraShake.Instance;
            if (!cam || p.shake <= 0f || p.shakeRange <= 0f) return;

            float d = Vector2.Distance(center, cam.transform.position);
            float near = 1f - Mathf.Clamp01(d / p.shakeRange);
            if (near > 0f) Siege.CameraShake.Kick(p.shake * near * near);
        }

        /// <summary>
        /// Set off the neighbours. They are armed rather than detonated: a barrel that goes off
        /// inside this call would run its own blast inside ours, which both nests unboundedly
        /// and lands as one flat bang. A fuse of a few frames makes it a chain you can watch
        /// travel down the row — and it is what stops two barrels from setting each other off
        /// forever, since an armed one ignores further triggers.
        /// </summary>
        private static void Chain(Vector2 center, ExplosionProfile p)
        {
            if (p.chainRadius <= 0f) return;

            var filter = new ContactFilter2D { useTriggers = true, useLayerMask = false };
            int count = Physics2D.OverlapCircle(center, p.chainRadius, filter, Hits);

            Caught.Clear();
            for (int i = 0; i < count; i++)
            {
                if (!Hits[i]) continue;
                var boom = Hits[i].GetComponentInParent<Explosive>();
                if (boom && !Caught.Contains(boom)) Caught.Add(boom);
            }

            foreach (var boom in Caught)
                boom.Chain(p.chainDelay + Random.Range(0f, p.chainJitter));
        }

        /// <summary>Outward from the blast, with a fallback for a target sitting exactly on it.</summary>
        private static Vector2 Away(Vector2 center, Vector2 point)
        {
            Vector2 d = point - center;
            return d.sqrMagnitude > 0.0001f ? d.normalized : Vector2.up;
        }
    }
}
