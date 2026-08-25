using System.Collections.Generic;
using UnityEngine;

namespace Spawners
{
    /// <summary>
    /// Drops creatures out of a chute. At runtime it does so on a timer and stops once enough of
    /// them are alive, the cap counting what is actually still walking so the line refills itself
    /// as whatever is downstream works through the backlog.
    ///
    /// In edit mode the same drop is a menu item on the component, and what it makes is a real
    /// prefab instance in the scene — selectable, movable, undoable, saved. Nothing is a ghost:
    /// what you put there while laying the line out is what play mode picks up, exactly as if you
    /// had dragged it in yourself.
    /// </summary>
    [AddComponentMenu("PhysFun/Enemy Factory")]
    public sealed class EnemyFactory : MonoBehaviour
    {
        /// <summary>The one creature in the project that has health to lose.</summary>
        private const string DefaultPrefab = "Prefabs/Enemies/Shotgunner";

        [Header("What")]
        [Tooltip("Creature to drop. Empty falls back to Resources/" + DefaultPrefab + ".")]
        [SerializeField] private GameObject prefab;

        [Tooltip("Where they come out. Defaults to this object.")]
        [SerializeField] private Transform mouth;

        [Header("When")]
        [Tooltip("Off makes this purely an authoring tool: it fills the scene when you ask it to " +
                 "and produces nothing on its own.")]
        [SerializeField] private bool runAtRuntime = true;

        [SerializeField] private float interval = 2.5f;

        [Tooltip("Stop dropping while this many are still alive. 0 = no cap.")]
        [SerializeField] private int maxAlive = 6;

        [Tooltip("Wait before the first one, so the scene is not already full on frame one.")]
        [SerializeField] private float startDelay = 1f;

        [Header("How")]
        [Tooltip("Velocity they leave the chute with, in the mouth's own space. Straight down is " +
                 "the obvious one; sideways gives whatever is downstream something to sort out.")]
        [SerializeField] private Vector2 ejectVelocity = new(0f, -1.5f);

        [Tooltip("Random spread across the mouth, in units.")]
        [SerializeField] private float spread = 0.25f;

        private readonly List<GameObject> _alive = new();
        private float _timer;

        /// <summary>How many of its creatures are still on their feet.</summary>
        public int AliveCount
        {
            get
            {
                Prune();
                return _alive.Count;
            }
        }

        private Transform Mouth => mouth ? mouth : transform;

        /// <summary>Resolved without writing the field, so a look in edit mode is not an edit.</summary>
        private GameObject Prefab => prefab ? prefab : Resources.Load<GameObject>(DefaultPrefab);

        private void OnEnable() => _timer = startDelay;

        private void Update()
        {
            if (!runAtRuntime || !Prefab) return;

            _timer -= Time.deltaTime;
            if (_timer > 0f) return;
            _timer = interval;

            Prune();
            if (maxAlive > 0 && _alive.Count >= maxAlive) return;

            Drop();
        }

        // ------------------------------------------------------------------ dropping

        /// <summary>
        /// Put one creature at the mouth. In play mode it is thrown out with the eject velocity
        /// and counted against the cap; in edit mode it is placed as a prefab instance and left
        /// for gravity to deal with once the game starts.
        /// </summary>
        [ContextMenu("Drop one")]
        public GameObject Drop()
        {
            var creature = Prefab;
            if (!creature) return null;

            Vector3 at = Mouth.position + Mouth.right * Random.Range(-spread, spread);

#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                var placed = (GameObject)UnityEditor.PrefabUtility.InstantiatePrefab(
                    creature, gameObject.scene);
                placed.transform.position = at;

                UnityEditor.Undo.RegisterCreatedObjectUndo(placed, "Drop creature");
                UnityEditor.Selection.activeGameObject = placed;
                return placed;
            }
#endif

            var go = Instantiate(creature, at, Quaternion.identity);

            var rb = go.GetComponent<Rigidbody2D>();
            if (rb) rb.linearVelocity = Mouth.TransformVector(ejectVelocity);

            _alive.Add(go);
            return go;
        }

        /// <summary>Fill the line up to the cap in one go — for laying a scene out by hand.</summary>
        [ContextMenu("Drop a full batch")]
        public void DropBatch()
        {
            int count = maxAlive > 0 ? maxAlive : 1;
            for (int i = 0; i < count; i++) Drop();
        }

        // Death replaces the creature with a corpse object, so the entry simply goes null.
        private void Prune()
        {
            for (int i = _alive.Count - 1; i >= 0; i--)
                if (!_alive[i])
                    _alive.RemoveAt(i);
        }

        private void OnDrawGizmosSelected()
        {
            var m = Mouth;

            Gizmos.color = Color.yellow;
            Gizmos.DrawLine(m.position - m.right * spread, m.position + m.right * spread);

            // Where the drop is thrown, and roughly how hard.
            Vector3 launch = m.TransformVector(ejectVelocity);
            if (launch.sqrMagnitude < 1e-4f) return;

            Gizmos.color = Color.red;
            Gizmos.DrawRay(m.position, launch * 0.4f);
        }
    }
}
