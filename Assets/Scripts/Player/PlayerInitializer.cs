using UnityEngine;

namespace Player
{
    public class PlayerInitializer : MonoBehaviour
    {
        private void Awake()
        {
            App.Instance.PlayerTransform = transform;
            App.Instance.PlayerGo = gameObject;
        }
    }
}