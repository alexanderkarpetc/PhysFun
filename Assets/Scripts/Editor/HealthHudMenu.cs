using Player;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Editor
{
    /// <summary>
    /// Drops the health bar into the open scene, already wired: a UIDocument pointed at the
    /// HealthBar UXML, sharing the panel the rest of the runtime UI draws on, plus the
    /// <see cref="HealthHud"/> that drives it. The bar finds the player on its own at runtime.
    /// </summary>
    public static class HealthHudMenu
    {
        private const string Uxml = "Assets/UI/Player/HealthBar.uxml";
        private const string Panel = "Assets/UI/Toolbox/PanelSettings.asset";

        [MenuItem("PhysFun/Create/Health Bar", false, 120)]
        private static void CreateHealthBar()
        {
            var existing = Object.FindFirstObjectByType<HealthHud>();
            if (existing)
            {
                Selection.activeGameObject = existing.gameObject;
                Debug.Log("[HealthHud] The scene already has one.", existing);
                return;
            }

            var go = new GameObject("HealthHud", typeof(UIDocument), typeof(HealthHud));

            var doc = go.GetComponent<UIDocument>();
            doc.panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>(Panel);
            doc.visualTreeAsset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(Uxml);

            // Above the toolbox panel (sorting order 0) so the bar is never covered by it.
            doc.sortingOrder = 10;

            Undo.RegisterCreatedObjectUndo(go, "Create Health Bar");
            Selection.activeGameObject = go;
        }
    }
}
