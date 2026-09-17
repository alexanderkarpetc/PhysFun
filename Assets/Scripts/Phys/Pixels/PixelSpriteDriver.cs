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
            FlameFieldView.Install();

            var go = new GameObject("~PixelSpriteDriver") { hideFlags = HideFlags.HideAndDontSave };
            _instance = go.AddComponent<PixelSpriteDriver>();
        }

        /// <summary>
        /// Log a breakdown whenever a frame takes longer than this, in milliseconds. 0 to stop.
        ///
        /// The point is to tell apart the two things that look identical from inside a stutter:
        /// this pipeline being slow, and the frame being slow around it. If the report says the
        /// whole pipeline took 4ms of a 900ms frame, the time went to physics — a burning object
        /// sheds bodies with ragged outlines, and overlapping ones cost the product of their
        /// collider complexity — and no amount of tuning the fire will touch it.
        /// </summary>
        public static float SpikeLogMs = 60f;

        private void LateUpdate()
        {
            bool timing = SpikeLogMs > 0f;
            var sw = timing ? System.Diagnostics.Stopwatch.StartNew() : null;
            double tFire = 0, tFlames = 0, tFlush = 0, tColliders = 0, tSplits = 0;

            FireSystem.Instance.Tick(Time.deltaTime);
            if (timing) tFire = sw.Elapsed.TotalMilliseconds;

            // Drives its own 60 Hz grid, and calls back into FireSystem.EmitFlames once per
            // grid frame — so flames are born and rise at Noita's rate, not at the burn rate.
            FlameField.Instance.Tick(Time.deltaTime);
            if (timing) tFlames = sw.Elapsed.TotalMilliseconds - tFire;

            var reg = PixelSpriteRegistry.Instance;
            reg.Flush();
            reg.CollectConsumed();
            if (timing) tFlush = sw.Elapsed.TotalMilliseconds - tFire - tFlames;

            reg.RefreshColliders(SimplifyLevel, ColliderBudgetMs);
            if (timing) tColliders = sw.Elapsed.TotalMilliseconds - tFire - tFlames - tFlush;

            if (Time.unscaledTime - _lastSplit > SplitInterval)
            {
                reg.ProcessSplits(SimplifyLevel);
                _lastSplit = Time.unscaledTime;
            }
            if (timing) tSplits = sw.Elapsed.TotalMilliseconds - tFire - tFlames - tFlush - tColliders;

            if (!timing) return;

            float frameMs = Time.unscaledDeltaTime * 1000f;
            double pipelineMs = sw.Elapsed.TotalMilliseconds;
            if (frameMs < SpikeLogMs && pipelineMs < SpikeLogMs) return;

            reg.CountColliders(out int paths, out int points);
            Debug.Log(
                $"[pixels] frame {frameMs:F0}ms, pipeline {pipelineMs:F1}ms " +
                $"(fire {tFire:F1} flames {tFlames:F1} upload {tFlush:F1} colliders {tColliders:F1} splits {tSplits:F1}) | " +
                $"objects {reg.RecordCount}, burns {FireSystem.Instance.BurnCount}, " +
                $"lit px {FireSystem.Instance.LitPixelCount}, flame cells {FlameField.Instance.Count}, " +
                $"collider paths {paths}, points {points}");
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
