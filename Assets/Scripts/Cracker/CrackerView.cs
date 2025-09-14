using UnityEngine;

namespace Cracker
{
    public class CrackerView : MonoBehaviour
    {
        public bool crackEnabled = true;
        [Min(0f)] public float radius = 2f;           // zone radius (renamed from crackdius)
        public LayerMask targetLayer = ~0;            // optional filter for future use

        Camera _cam;

        void Awake() => _cam = Camera.main;

        void Update()
        {
            if (!crackEnabled || _cam == null) return;

            // follow cursor in world space; stay on current Z plane
            Vector3 m = Input.mousePosition;
            Vector3 w = _cam.ScreenToWorldPoint(m);
            w.z = transform.position.z;
            transform.position = w;

            // right-click to trigger crack
            if (Input.GetMouseButtonDown(1))
                Crack();
        }

        public void Crack()
        {
            Vector3 wp = _cam.ScreenToWorldPoint(Input.mousePosition);
            wp.z = 0f;
            var hits = Physics2D.OverlapCircleAll(wp, radius, targetLayer);
            foreach (var h in hits)
            {
                Cracker.Crack(h.gameObject, 6);
            }
                
            
        }

        // Scene view visual for the zone
        void OnDrawGizmos()
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, radius);
        }
    }
}