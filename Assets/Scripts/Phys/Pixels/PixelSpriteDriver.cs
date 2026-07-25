using Phys.Fire;
using UnityEngine;

namespace Phys.Pixels
{
    /// <summary>
    /// Single owner of the per-frame pixel pipeline. Self-installs on play so any
    /// system can write pixels without also having to remember to flush them.
    ///
    /// Order matters: fire writes pixels, then the registry uploads them, drops
    /// objects that were fully consumed, retraces colliders under a time budget,
    /// and finally (on a throttle) runs the expensive split flood fill.
    /// </summary>
    [DefaultExecutionOrder(1000)]
    public sealed class PixelSpriteDriver : MonoBehaviour
    {
        /// <summary>RDP level used for every runtime collider retrace.</summary>
        public static int SimplifyLevel = 2;

        /// <summary>Per-frame time budget for collider retraces.</summary>
        public static float ColliderBudgetMs = 3f;

        /// <summary>Seconds between split (flood fill) checks.</summary>
        public static float SplitInterval = 0.15f;

        private static PixelSpriteDriver _instance;
        private float _lastSplit;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            if (_instance) return;
            // Both singletons are reset by SubsystemRegistration hooks whose order is
            // undefined, so the wiring has to happen out here, after they both exist.
            FireSystem.Instance.Bind(PixelSpriteRegistry.Instance);

            var go = new GameObject("~PixelSpriteDriver") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<PixelSpriteDriver>();
        }

        private void LateUpdate()
        {
            FireSystem.Instance.Tick(Time.deltaTime);

            var reg = PixelSpriteRegistry.Instance;
            reg.Flush();
            reg.CollectConsumed();
            reg.RefreshColliders(SimplifyLevel, ColliderBudgetMs);

            if (Time.unscaledTime - _lastSplit > SplitInterval)
            {
                reg.ProcessSplits(SimplifyLevel);
                _lastSplit = Time.unscaledTime;
            }
        }

        /// <summary>
        /// Run the whole pipeline right now with no budget. Use at the end of an
        /// interaction (an erase stroke, say) so the result settles immediately.
        /// </summary>
        public static void FinalizeNow()
        {
            var reg = PixelSpriteRegistry.Instance;
            reg.Flush();
            reg.CollectConsumed();
            reg.ProcessSplits(SimplifyLevel, force: true);
            reg.RefreshColliders(SimplifyLevel, force: true);
            if (_instance) _instance._lastSplit = Time.unscaledTime;
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }
    }
}
