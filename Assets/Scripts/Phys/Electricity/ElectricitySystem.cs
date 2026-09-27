using System.Collections.Generic;
using Common;
using Materials;
using Phys.Fire;
using Phys.Pixels;
using UnityEngine;

namespace Phys.Electricity
{
    /// <summary>
    /// One discharge, everything it does. Call <see cref="Strike"/> from wherever the charge
    /// came from — a debug zap, a broken cable, a trap — and hand it an
    /// <see cref="ElectricityProfile"/>.
    ///
    /// Electricity is the first thing in this game that does almost nothing where you point it.
    /// A bolt into open air is a spark and a scorch mark; the same bolt into something with
    /// <see cref="PhysMaterial.Conducts"/> set finds every other conductor that one is touching
    /// and hurts whoever is leaning on any of them, however far down the chain. That is the
    /// whole reason the metal material exists, and it is also Noita's model: conduction lives on
    /// the material and nowhere else, and the system's only question of the world is
    /// CellConductsElectricity.
    ///
    /// The work splits three ways and each is settled once, here, at strike time:
    /// <list type="bullet">
    /// <item><b>the network</b> — a flood out from whatever caught the bolt, conductor to
    ///       touching conductor,</item>
    /// <item><b>the shock</b> — direct damage inside the strike itself, conducted damage to
    ///       anything touching an energised body,</item>
    /// <item><b>the charge</b> — handed to <see cref="ArcField"/>, which keeps the whole network
    ///       visibly live for the next half second, conductor after conductor down the chain,
    ///       and sets light to what is touching it.</item>
    /// </list>
    /// </summary>
    public static class ElectricitySystem
    {
        // One discharge at a time, so these are shared rather than allocated per strike.
        private static readonly Collider2D[] Hits = new Collider2D[256];
        private static readonly List<Collider2D> Network = new();
        private static readonly List<int> Depth = new();
        private static readonly Queue<int> Frontier = new();
        private static readonly Dictionary<Damageable, Shock> Victims = new();

        private readonly struct Shock
        {
            public readonly float Amount;
            public readonly Vector2 Point;

            /// <summary>Where the charge jumped into them from, and how far down the chain that was.</summary>
            public readonly Vector2 From;
            public readonly int Depth;

            public Shock(float amount, Vector2 point, Vector2 from, int depth)
            {
                Amount = amount;
                Point = point;
                From = from;
                Depth = depth;
            }
        }

        /// <summary>
        /// Let one go at <paramref name="origin"/>. Returns how many conductors it got into,
        /// which is 0 for a bolt that found nothing but air.
        /// </summary>
        /// <param name="source">What to blame for the damage.</param>
        public static int Strike(Vector2 origin, ElectricityProfile p, GameObject source = null)
        {
            if (p == null || p.strikeRadius <= 0f) return 0;

            Network.Clear();
            Depth.Clear();
            Victims.Clear();

            var charge = new Charge { Profile = p, Source = source, Origin = origin };

            Seed(origin, p, charge);
            Spread(p, charge);
            Shocked(origin, p);
            Hurt(p, source, charge);
            Burn(origin, p);

            charge.Conductors.AddRange(Network);
            charge.Depth.AddRange(Depth);
            ArcField.Instance.Spawn(charge);

            if (p.cameraShake > 0f) Siege.CameraShake.Kick(p.cameraShake);

            int reached = Network.Count;
            Network.Clear();
            Depth.Clear();
            Victims.Clear();
            return reached;
        }

        // ─────────────────────────────────────────────────────────────────────────
        // The network
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>Whatever conducts and is close enough to the bolt to catch it.</summary>
        private static void Seed(Vector2 origin, ElectricityProfile p, Charge charge)
        {
            int count = Physics2D.OverlapCircle(
                origin, p.strikeRadius + PixelSpriteRegistry.QueryMargin, Filter(p), Hits);

            for (int i = 0; i < count && Network.Count < p.maxConductors; i++)
            {
                var col = Hits[i];
                if (!col || !Conducts(col) || Network.Contains(col)) continue;

                Network.Add(col);
                Depth.Add(0);
                charge.Hops.Add(new Hop(origin, col.ClosestPoint(origin), 0));
            }
        }

        /// <summary>
        /// Out from the seeds, conductor to touching conductor. The gap a charge will cross is
        /// the material's own <see cref="PhysMaterial.ArcJumpGap"/> rather than a figure on the
        /// profile: how well two things are joined is a property of what they are made of, not
        /// of what hit them.
        /// </summary>
        private static void Spread(ElectricityProfile p, Charge charge)
        {
            Frontier.Clear();
            for (int i = 0; i < Network.Count; i++) Frontier.Enqueue(i);

            var filter = Filter(p);

            while (Frontier.Count > 0 && Network.Count < p.maxConductors)
            {
                int fromIndex = Frontier.Dequeue();
                var from = Network[fromIndex];
                if (!from) continue;

                float gap = MaterialLibrary.Of(from.gameObject).ArcJumpGap;
                var b = from.bounds;
                var size = (Vector2)b.size + Vector2.one * (gap * 2f);

                int count = Physics2D.OverlapBox(b.center, size, 0f, filter, Hits);
                for (int i = 0; i < count && Network.Count < p.maxConductors; i++)
                {
                    var col = Hits[i];
                    if (!col || col == from || !Conducts(col)) continue;
                    if (Network.Contains(col)) continue;

                    // OverlapBox works on the bounding box, which for a long girder at an angle
                    // is far more than the girder. This is the real distance between the two.
                    var d = from.Distance(col);
                    if (d.distance > gap) continue;

                    int depth = Depth[fromIndex] + 1;
                    Network.Add(col);
                    Depth.Add(depth);
                    Frontier.Enqueue(Network.Count - 1);
                    charge.Hops.Add(new Hop(d.pointA, d.pointB, depth));
                }
            }

            Frontier.Clear();
        }

        private static bool Conducts(Collider2D col) =>
            MaterialLibrary.Of(col.gameObject).Conducts;

        // ─────────────────────────────────────────────────────────────────────────
        // The shock
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Who is in it. Two ways to be: standing in the bolt, or touching something the bolt
        /// got into. The second is the one that matters — it is how a discharge across the room
        /// reaches someone who never saw it.
        /// </summary>
        private static void Shocked(Vector2 origin, ElectricityProfile p)
        {
            var filter = Filter(p);

            if (p.directDamage > 0f)
            {
                int count = Physics2D.OverlapCircle(
                    origin, p.strikeRadius + PixelSpriteRegistry.QueryMargin, filter, Hits);

                for (int i = 0; i < count; i++)
                {
                    var col = Hits[i];
                    if (!col) continue;
                    if (Network.Contains(col)) continue;
                    Keep(col, p.directDamage, col.ClosestPoint(origin), origin, 0, p);
                }
            }

            if (p.conductedDamage <= 0f && p.conductorDamage <= 0f) return;

            // Snapshot the count: a conductor killed by its own shock could otherwise be
            // stepped on mid-loop.
            for (int n = 0; n < Network.Count; n++)
            {
                var wire = Network[n];
                if (!wire) continue;

                var b = wire.bounds;
                var size = (Vector2)b.size + Vector2.one * (p.contactGap * 2f + PixelSpriteRegistry.QueryMargin);

                int count = Physics2D.OverlapBox(b.center, size, 0f, filter, Hits);
                for (int i = 0; i < count; i++)
                {
                    var col = Hits[i];
                    if (!col) continue;

                    // A conductor is the thing doing the hurting; whether it is hurt back is a
                    // separate figure, and 0 by default.
                    bool isWire = col == wire || Network.Contains(col);
                    float amount = isWire ? p.conductorDamage : p.conductedDamage;
                    if (amount <= 0f) continue;

                    var d = wire.Distance(col);
                    if (!isWire && d.distance > p.contactGap) continue;

                    if (isWire) Keep(col, amount, b.center, b.center, Depth[n], p);
                    else Keep(col, amount, d.pointB, d.pointA, Depth[n], p);
                }
            }
        }

        /// <summary>Hardest shock wins: several colliders on one body is still one victim.</summary>
        private static void Keep(Collider2D col, float amount, Vector2 point, Vector2 from, int depth,
                                 ElectricityProfile p)
        {
            if (amount < p.minDamage) return;

            var victim = col.GetComponentInParent<Damageable>();
            if (!victim || victim.IsDead) return;

            if (Victims.TryGetValue(victim, out var had) && had.Amount >= amount) return;
            Victims[victim] = new Shock(amount, point, from, depth);
        }

        private static void Hurt(ElectricityProfile p, GameObject source, Charge charge)
        {
            foreach (var pair in Victims)
            {
                var victim = pair.Key;
                if (!victim || victim.IsDead) continue;

                // No direction and no impulse: a shock does not arrive from anywhere and does
                // not throw a corpse. The blood it draws wells up rather than spraying, which
                // is what Damageable does with a directionless hit already.
                var shock = pair.Value;
                victim.ApplyDamage(new DamageInfo(
                    shock.Amount, DamageType.Electric, shock.Point, source: source));

                // A metal thing hurt by its own charge has nothing to jump across.
                if ((shock.From - shock.Point).sqrMagnitude > 1e-6f)
                    charge.Taps.Add(new Hop(shock.From, shock.Point, shock.Depth));
            }
        }

        // ─────────────────────────────────────────────────────────────────────────
        // What it leaves behind
        // ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// The strike point itself lights whatever will burn. Everything further along is the
        /// charge's own doing, rolled every redraw on the outline of each live conductor.
        /// </summary>
        private static void Burn(Vector2 origin, ElectricityProfile p)
        {
            if (p.igniteChancePercent <= 0f) return;
            FireSystem.Instance.IgniteAt(origin, p.strikeRadius * 0.5f);
        }

        private static ContactFilter2D Filter(ElectricityProfile p) => new()
        {
            useTriggers = false,
            useLayerMask = true,
            layerMask = p.affects,
        };
    }
}
