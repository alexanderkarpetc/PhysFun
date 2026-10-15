using UnityEngine;

namespace Props
{
    /// <summary>
    /// Hidden host that checks, a few each physics step, whether sleeping <see cref="Decor"/>
    /// still has something under it. One host rather than a FixedUpdate on every piece of
    /// clutter: a furnished floor holds hundreds of them, and only a dozen are looked at a step.
    /// </summary>
    public sealed class DecorFooting : MonoBehaviour
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            foreach (var stale in Resources.FindObjectsOfTypeAll<DecorFooting>())
                if (stale) Destroy(stale.gameObject);
            var go = new GameObject("~DecorFooting") { hideFlags = HideFlags.HideInHierarchy };
            DontDestroyOnLoad(go);
            go.AddComponent<DecorFooting>();
        }

        private void FixedUpdate() => Decor.CheckFooting();
    }
}
