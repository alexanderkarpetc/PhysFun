using UnityEngine;

namespace Ragdolls
{
    /// <summary>
    /// Sits on a live creature and swaps it for its corpse. The pose is read off the sprite
    /// the animator happens to be showing, so the ragdoll starts in exactly the frame the
    /// creature died on instead of snapping to a T-pose.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class RagdollSpawner : MonoBehaviour
    {
        [Header("Refs")]
        [SerializeField] private GameObject ragdollPrefab;

        [Tooltip("Animated renderer. Its sprite names the death pose and its transform is the spawn origin.")]
        [SerializeField] private SpriteRenderer poseSource;

        [Tooltip("Transform whose negative X scale means 'facing left'. Defaults to the pose source.")]
        [SerializeField] private Transform facingSource;

        [Tooltip("Body whose velocity the corpse inherits.")]
        [SerializeField] private Rigidbody2D body;

        [Header("Tuning")]
        [Range(0f, 2f)]
        [SerializeField] private float inheritVelocity = 1f;

        [Tooltip("Random torque impulse per piece, so a corpse never lands the same way twice.")]
        [SerializeField] private float spin = 0.05f;

        [Tooltip("Destroy the creature once the corpse is up. Off leaves it to the caller.")]
        [SerializeField] private bool destroySource = true;

        private bool _spawned;

        private void Reset()
        {
            poseSource = GetComponentInChildren<SpriteRenderer>();
            body = GetComponent<Rigidbody2D>();
            facingSource = poseSource ? poseSource.transform : null;
        }

        /// <summary>Swap the creature for its corpse. Safe to call twice — only the first one lands.</summary>
        public Ragdoll Spawn(Vector2 impulse = default, Vector2 hitPoint = default)
        {
            if (_spawned) return null;
            _spawned = true;

            if (ragdollPrefab == null)
            {
                Debug.LogWarning($"{name}: no ragdoll prefab assigned", this);
                return null;
            }

            Transform origin = poseSource ? poseSource.transform : transform;
            Transform facing = facingSource ? facingSource : origin;
            bool flipX = facing.lossyScale.x < 0f || (poseSource && poseSource.flipX);

            var go = Instantiate(ragdollPrefab, origin.position, Quaternion.identity);

            // The corpse art is authored at the creature's own pixel scale; a scaled-up
            // enemy has to leave a scaled-up body behind.
            float scale = Mathf.Abs(origin.lossyScale.y);
            if (!Mathf.Approximately(scale, 1f))
                go.transform.localScale = new Vector3(scale, scale, 1f);

            var ragdoll = go.GetComponent<Ragdoll>();
            if (ragdoll)
            {
                ragdoll.ApplySpritePose(poseSource ? poseSource.sprite : null, flipX);

                if (body && inheritVelocity > 0f)
                    ragdoll.SetVelocity(body.linearVelocity * inheritVelocity);

                if (impulse != Vector2.zero || spin > 0f)
                    ragdoll.AddImpulse(impulse, hitPoint == default ? (Vector2)origin.position : hitPoint, spin);
            }

            if (destroySource) Destroy(gameObject);
            return ragdoll;
        }
    }
}
