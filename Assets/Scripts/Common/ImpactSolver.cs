using Materials;
using UnityEngine;

namespace Common
{
    /// <summary>What one physics contact turned out to be worth.</summary>
    public readonly struct ImpactResult
    {
        /// <summary>Damage the hit earned. Zero means there was nothing worth reporting.</summary>
        public readonly float Amount;

        /// <summary>The approach speed it was charged for — the attacker's own, along the normal.</summary>
        public readonly float Speed;

        /// <summary>Momentum behind the hit (effective mass * speed), for knockback and corpse kicks.</summary>
        public readonly float Momentum;

        public readonly Vector2 Point;

        /// <summary>Unit vector along the push, pointing into the victim.</summary>
        public readonly Vector2 Normal;

        public bool Landed => Amount > 0f;

        public ImpactResult(float amount, float speed, float momentum, Vector2 point, Vector2 normal)
        {
            Amount = amount;
            Speed = speed;
            Momentum = momentum;
            Point = point;
            Normal = normal;
        }

        /// <summary>Package it as a hit. <paramref name="kick"/> scales the corpse impulse.</summary>
        public DamageInfo ToDamage(GameObject source, float kick) =>
            new(Amount, DamageType.Impact, Point, Normal, Normal * (Momentum * kick), source);
    }

    /// <summary>
    /// The physics half of the damage model: pure maths over a <see cref="Collision2D"/>, no
    /// state and no side effects, so the rules live in one readable place.
    ///
    /// The rule that shapes everything else: <b>a hit is only ever charged for the attacker's
    /// own motion.</b> Run into a wall, fall onto a floor, dive onto a crate — the thing you
    /// touched brought nothing with it, so it costs nothing. There is deliberately no fall
    /// damage in this game and none has to be special-cased away: it simply never arises.
    /// Drop that same crate on someone's head and it is the crate that brought the speed.
    /// </summary>
    public static class ImpactSolver
    {
        /// <summary>Contacts averaged per collision. A flat landing rarely reports more.</summary>
        private const int MaxContacts = 4;

        /// <summary>
        /// Weigh a fresh collision from the victim's side. Returns a zero result when the hit is
        /// too gentle, self-inflicted, or came from something standing still.
        ///
        /// <paramref name="victimVelocity"/> must be the victim's velocity from *before* the
        /// physics step that produced this contact — see the note on pre-impact speed below.
        /// </summary>
        public static ImpactResult Evaluate(Collision2D c, Rigidbody2D victim, Vector2 victimVelocity,
                                            ImpactDamageConfig cfg)
        {
            if (c == null || !victim || cfg == null || c.contactCount == 0) return default;

            var attacker = c.rigidbody;
            if (!attacker || attacker == victim) return default;

            // Average the contacts: a crate landing flat reports several with the same normal,
            // and averaging keeps a single corner touch from reading as the whole blow.
            int count = Mathf.Min(c.contactCount, MaxContacts);
            Vector2 center = victim.worldCenterOfMass;
            Vector2 point = Vector2.zero;
            Vector2 normal = Vector2.zero;
            for (int i = 0; i < count; i++)
            {
                var contact = c.GetContact(i);
                point += contact.point;
                normal += Orient(contact.normal, contact.point, center);
            }
            point /= count;
            if (normal.sqrMagnitude < 1e-6f) return default;
            normal.Normalize();

            // Collision callbacks run *after* the solver has already dealt with the contact, so
            // reading either body's velocity here reports the rebound, not the blow: a crate that
            // has just landed says it is barely moving. Unity hands us relativeVelocity precisely
            // because it was captured before the solve, and it is the only pre-impact figure
            // available — so the whole rule is derived from it.
            //
            // Its normal component is the closing speed. The attacker's own share follows from
            // vAttacker*n = (vAttacker - vVictim)*n + vVictim*n, using the victim's velocity from
            // before the step (the caller cached it). Charging the smaller of the two is what
            // keeps a landing free and a dropped rock expensive.
            float closing = Mathf.Abs(Vector2.Dot(c.relativeVelocity, normal));
            float driving = closing + Vector2.Dot(victimVelocity, normal);
            float speed = Mathf.Min(closing, driving);
            if (speed <= cfg.minSpeed) return default;

            float mass = attacker.mass;
            // Anything driven rather than falling — a crusher, a lift — cannot be slowed by what
            // it hits, so it swings a weight class instead of its Rigidbody mass.
            if (attacker.bodyType != RigidbodyType2D.Dynamic)
                mass = Mathf.Max(mass, cfg.immovableMass);
            mass = Mathf.Min(mass, cfg.massCap);

            float fromAbove = Mathf.Clamp01(-normal.y);   // normal pushes into us; downward = from overhead
            float material = MaterialLibrary.Of(attacker.gameObject).ImpactDamageMultiplier;

            float amount = cfg.scale
                           * Mathf.Pow(mass, cfg.massExponent)
                           * Mathf.Pow(speed, cfg.speedExponent)
                           * material
                           * Mathf.Lerp(cfg.lateralMultiplier, 1f, fromAbove);

            amount = Mathf.Min(amount, cfg.maxDamagePerHit);
            if (amount < cfg.minDamage) return default;

            if (cfg.logHits)
                Debug.Log($"[Impact] {attacker.name} -> {victim.name}: {amount:F1} " +
                          $"(speed {speed:F1} of closing {closing:F1}, mass {mass:F0}, " +
                          $"above {fromAbove:F2}, material x{material:F2})", victim);

            return new ImpactResult(amount, speed, mass * speed, point, normal);
        }

        /// <summary>
        /// Add this collision's share of the squeeze on <paramref name="victim"/> to a running
        /// total. Call it for every collision the victim has in a step, then read the result as
        /// <c>scalar - vector.magnitude</c>.
        ///
        /// The trick is that the two totals only disagree when forces oppose each other. Standing
        /// on the ground, the one contact holding you up counts the same in both, so the
        /// difference is zero. Put a block on your head and the ground has to push harder while
        /// the block pushes down: the magnitudes add up, the vectors cancel, and what is left over
        /// is exactly the part that is squeezing rather than carrying.
        ///
        /// Returns true when the pressure came from a body that can actually move — a fallen rock,
        /// a driven mechanism. Standing terrain squeezing you is a collider you clipped into, not
        /// a crushing, and <see cref="Damageable"/> uses this to tell the two apart.
        /// </summary>
        public static bool AccumulateSqueeze(Collision2D c, Rigidbody2D victim, ref float scalar, ref Vector2 vector)
        {
            if (c == null || !victim) return false;

            Vector2 center = victim.worldCenterOfMass;
            float added = 0f;
            int count = c.contactCount;
            for (int i = 0; i < count; i++)
            {
                var contact = c.GetContact(i);
                float impulse = Mathf.Abs(contact.normalImpulse);
                if (impulse <= 0f) continue;

                added += impulse;
                scalar += impulse;
                vector += Orient(contact.normal, contact.point, center) * impulse;
            }

            var other = c.rigidbody;
            return added > 0f && other && other.bodyType != RigidbodyType2D.Static;
        }

        /// <summary>
        /// Flip a contact normal so it points from the contact into the victim — the direction the
        /// other body is pushing. Unity's own orientation depends on which collider the physics
        /// engine happened to list first, which is not something the damage rules should care about.
        /// </summary>
        private static Vector2 Orient(Vector2 normal, Vector2 point, Vector2 center) =>
            Vector2.Dot(normal, center - point) < 0f ? -normal : normal;
    }
}
