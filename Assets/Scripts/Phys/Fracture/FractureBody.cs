using UnityEngine;

namespace Phys.Fracture
{
    /// <summary>
    /// Routes ordinary physics contacts into <see cref="FractureSystem"/>, so brittle material
    /// splits when something heavy arrives on it and not only when it is shot.
    ///
    /// Added and removed by <see cref="Materials.MaterialView.Apply"/> off the back of the
    /// material, so nothing has to remember to wire it up — terrain chunks, spawned props,
    /// shards and split pieces all get it or don't get it for the same reason.
    ///
    /// The rule it charges by is the one <see cref="Common.ImpactSolver"/> already uses: only
    /// the thing that brought the speed pays. Ice does not crack because you walked into it.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class FractureBody : MonoBehaviour
    {
        [Tooltip("Momentum-to-damage conversion, so one figure of force feeds the fracture " +
                 "model whether it arrived as a bullet or as a boulder.")]
        [SerializeField] private float impactScale = 0.25f;

        [Tooltip("Seconds before this body will take another crack. A boulder rolling down a " +
                 "frozen slope reports a contact every step, and each one is not a fracture.")]
        [SerializeField] private float cooldown = 0.25f;

        private float _nextHit;

        private void OnCollisionEnter2D(Collision2D c)
        {
            if (Time.time < _nextHit) return;

            var attacker = c.rigidbody;
            // Geometry with no body of its own carries no momentum, and a body that is being
            // pushed rather than arriving is the ice's problem, not the ice's fault.
            if (!attacker || attacker.bodyType != RigidbodyType2D.Dynamic) return;
            if (c.contactCount == 0) return;

            var contact = c.GetContact(0);
            Vector2 center = c.otherCollider ? (Vector2)c.otherCollider.bounds.center
                                             : (Vector2)transform.position;

            // Unity's normal orientation depends on which collider it happened to list first;
            // point it into us, which is the direction the hit is travelling.
            Vector2 normal = contact.normal;
            if (Vector2.Dot(normal, center - contact.point) < 0f) normal = -normal;

            float speed = Mathf.Abs(Vector2.Dot(c.relativeVelocity, normal));
            float force = attacker.mass * speed * impactScale;

            // Crack the collider that was actually hit, not whatever owns the body. On a welded
            // terrain piece those are different objects: the rigidbody sits on the parent and
            // the sprite — the thing with pixels to cut — is the chunk underneath it.
            var target = c.otherCollider ? c.otherCollider.gameObject : gameObject;

            if (!FractureSystem.Hit(target, contact.point, normal, force)) return;
            _nextHit = Time.time + cooldown;
        }
    }
}
