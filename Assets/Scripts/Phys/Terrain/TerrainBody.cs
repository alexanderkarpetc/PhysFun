using System.Collections.Generic;
using Spawners;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// Marks a sprite object as destructible <em>terrain</em>: it stands still as a static
    /// body for as long as it is still connected — through other anchored terrain — to
    /// something immovable (the map borders). <see cref="TerrainSupportSystem"/> runs that
    /// reachability check and calls <see cref="Detach"/> on everything it can't reach, which
    /// is what turns a carved-out lump into a falling rock.
    ///
    /// Nothing has to be wired up per piece: the eraser, fire and the cracker all produce
    /// new pieces by cloning the object they cut, so pieces arrive with this component
    /// already attached and register themselves the moment they're instantiated.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class TerrainBody : MonoBehaviour
    {
        [Tooltip("Static while true. Cleared for good once the piece breaks loose.")]
        [SerializeField] private bool anchored = true;

        [Tooltip("Never falls, whatever happens around it. For terrain you always want in place.")]
        [SerializeField] private bool bedrock;

        [Tooltip("Sorting order applied once the piece breaks loose, so debris reads as a prop " +
                 "rather than as background terrain.")]
        [SerializeField] private int detachedSortingOrder;

        public bool Anchored => anchored;
        public bool Bedrock => bedrock;

        /// <summary>True when <paramref name="go"/> is still part of the standing terrain.</summary>
        public static bool IsAnchored(GameObject go)
        {
            if (!go) return false;
            var body = go.GetComponent<TerrainBody>();
            return body && body.anchored;
        }

        /// <summary>Tag <paramref name="go"/> as standing terrain and make its body static.</summary>
        public static TerrainBody Apply(GameObject go, bool bedrock = false)
        {
            if (!go) return null;
            var body = go.GetComponent<TerrainBody>();
            if (!body) body = go.AddComponent<TerrainBody>();
            body.anchored = true;
            body.bedrock = bedrock;

            var rb = go.GetComponent<Rigidbody2D>();
            if (rb) rb.bodyType = RigidbodyType2D.Static;

            TerrainSupportSystem.Register(body);
            return body;
        }

        /// <summary>
        /// Stop being standing terrain, without taking a body of its own. This is the half of
        /// breaking loose that <see cref="TerrainPiece"/> needs: a chunk that is about to be
        /// welded into a bigger piece must not arrive carrying a rigidbody, because a collider
        /// belongs to the nearest rigidbody above it and one of its own would keep it separate.
        ///
        /// Returns false when the piece was already loose, so callers can tell a real detach
        /// from a repeat.
        /// </summary>
        public bool Release()
        {
            if (!anchored) return false;
            anchored = false;
            bedrock = false;
            TerrainSupportSystem.Unregister(this);

            var sr = GetComponent<SpriteRenderer>();
            if (sr) sr.sortingOrder = detachedSortingOrder;
            return true;
        }

        /// <summary>Break loose on its own: a free rigid body, out of the support checks.</summary>
        public void Detach()
        {
            if (!Release()) return;

            var rb = GetComponent<Rigidbody2D>();
            if (!rb) rb = gameObject.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Dynamic;
            rb.simulated = true;
            MassRecalculator.SetMass(null, rb, GetComponent<Collider2D>());
        }

        public static void Detach(GameObject go)
        {
            if (!go) return;
            var body = go.GetComponent<TerrainBody>();
            if (body) body.Detach();
        }

        /// <summary>Detach every piece that is terrain; anything else is left alone.</summary>
        public static void DetachAll(IReadOnlyList<GameObject> pieces)
        {
            if (pieces == null) return;
            for (int i = 0; i < pieces.Count; i++) Detach(pieces[i]);
        }

        private void OnEnable()
        {
            if (anchored) TerrainSupportSystem.Register(this);
        }

        private void OnDisable() => TerrainSupportSystem.Unregister(this);
    }
}
