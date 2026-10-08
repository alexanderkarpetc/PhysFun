using UnityEngine;

namespace Rooms
{
    /// <summary>Draws a built floor's plan in the scene view: room boxes, links, corridor routes.</summary>
    public sealed class FloorGizmos : MonoBehaviour
    {
        private FloorLayout _plan;

        public void Set(FloorLayout plan) => _plan = plan;

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            if (_plan == null) return;
            Gizmos.color = new Color(0.6f, 0.7f, 0.8f, 0.5f);
            foreach (var r in _plan.Rects) Gizmos.DrawWireCube(r.center, r.size);
            Gizmos.color = new Color(0.47f, 0.79f, 0.84f, 0.9f);
            foreach (var route in _plan.Corridors)
                for (int i = 1; i < route.Count; i++)
                    Gizmos.DrawLine(route[i - 1], route[i]);
        }
#endif
    }
}
