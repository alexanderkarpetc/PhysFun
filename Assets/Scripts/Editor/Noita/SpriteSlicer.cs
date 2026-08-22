using System.Collections.Generic;
using UnityEditor;
using UnityEditor.U2D.Sprites;
using UnityEngine;

namespace NoitaImport
{
    /// <summary>One sprite to carve out of a sheet. Pixel rect plus a normalised pivot.</summary>
    public struct SliceSpec
    {
        public string Name;
        public Rect Rect;
        public Vector2 Pivot;
    }

    /// <summary>
    /// Writes sprite rects onto a texture importer.
    ///
    /// Unity 6 dropped support for TextureImporter.spritesheet — assigning it is a silent
    /// no-op now — so the slices go through the sprite editor data provider instead. Sprite
    /// ids are carried over by name, which is what keeps prefabs and definitions pointing at
    /// the same sprites when a creature is re-imported.
    /// </summary>
    public static class SpriteSlicer
    {
        public static bool Apply(TextureImporter importer, IReadOnlyList<SliceSpec> slices)
        {
            if (importer == null || slices == null || slices.Count == 0) return false;

            var factories = new SpriteDataProviderFactories();
            factories.Init();

            var provider = factories.GetSpriteEditorDataProviderFromObject(importer);
            if (provider == null)
            {
                Debug.LogError($"No sprite data provider for {importer.assetPath} — is the 2D Sprite package installed?");
                return false;
            }

            provider.InitSpriteEditorDataProvider();

            var keepIds = new Dictionary<string, GUID>();
            foreach (var existing in provider.GetSpriteRects())
                keepIds[existing.name] = existing.spriteID;

            var rects = new SpriteRect[slices.Count];
            for (int i = 0; i < slices.Count; i++)
            {
                var s = slices[i];
                rects[i] = new SpriteRect
                {
                    name = s.Name,
                    rect = s.Rect,
                    alignment = SpriteAlignment.Custom,
                    pivot = s.Pivot,
                    border = Vector4.zero,
                    spriteID = keepIds.TryGetValue(s.Name, out var id) ? id : GUID.Generate()
                };
            }

            provider.SetSpriteRects(rects);

            // Sprites are addressed by a name→fileId table as well; without refreshing it the
            // renamed or newly added slices come back as missing references.
            if (provider.GetDataProvider<ISpriteNameFileIdDataProvider>() is { } nameProvider)
            {
                var pairs = new List<SpriteNameFileIdPair>(rects.Length);
                foreach (var r in rects) pairs.Add(new SpriteNameFileIdPair(r.name, r.spriteID));
                nameProvider.SetNameFileIdPairs(pairs);
            }

            provider.Apply();

            if (provider.targetObject is AssetImporter target)
            {
                EditorUtility.SetDirty(target);
                target.SaveAndReimport();
            }

            return true;
        }
    }
}
