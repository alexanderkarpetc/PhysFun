using System;
using System.Collections.Generic;
using Spawners;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;

public class SynthesizerView : MonoBehaviour
{
    [Header("UI")]
    public Button _showButton;
    public Button _createButton;
    public Button _cleanButton;
    public GameObject paintArea;
    public RectTransform sketchArea;   // RawImage RectTransform
    public Camera uiCam;               // null for ScreenSpace-Overlay, canvas.worldCamera otherwise
    public RawImage sketchImage;       // assign the RawImage component

    [Header("Canvas Texture")]
    public int texWidth = 500;
    public int texHeight = 500;
    public Color32 background = new Color32(0,0,0,0);   // transparent bg
    public Color32 penColor = new Color32(255,255,255,255);
    public int brushRadiusPx = 8;                       // pen radius in pixels
    public float pixelsPerUnit = 100f;                  // for the final sprite

    [Serializable] public class SpriteEvent : UnityEvent<Sprite> {}
    public SpriteEvent OnSpriteCreated;                 // call your outer logic here

    Texture2D _tex;
    bool _isDrawing;
    Vector2Int _lastPix;
    bool _hasLast;

    void Awake()
    {
        if (!uiCam) uiCam = Camera.main;
        InitTexture();
    }

    void OnEnable()
    {
        _showButton.onClick.AddListener(TogglePanel);
        _createButton.onClick.AddListener(CreateSprite);
        _cleanButton.onClick.AddListener(Clean);
    }

    void OnDisable()
    {
        _showButton.onClick.RemoveListener(TogglePanel);
        _createButton.onClick.RemoveListener(CreateSprite);
        _cleanButton.onClick.RemoveListener(Clean);
    }

    void InitTexture()
    {
        _tex = new Texture2D(texWidth, texHeight, TextureFormat.ARGB32, false);
        _tex.wrapMode = TextureWrapMode.Clamp;
        _tex.filterMode = FilterMode.Point;

        // clear
        var px = new Color32[texWidth * texHeight];
        for (int i = 0; i < px.Length; i++) px[i] = background;
        _tex.SetPixels32(px);
        _tex.Apply(false, false);

        if (sketchImage) sketchImage.texture = _tex;
    }

    void Update()
    {
        if (!sketchArea || !_tex) return;

        bool over = IsMouseOverSketchArea(sketchArea);
        if (Input.GetMouseButtonDown(0) && over)
        {
            _isDrawing = true;
            _hasLast = false;
        }

        if (_isDrawing && Input.GetMouseButton(0))
        {
            if (TryScreenToPixel(Input.mousePosition, out var p))
            {
                if (!_hasLast)
                {
                    StampDisc(p.x, p.y, brushRadiusPx, penColor);
                    _hasLast = true;
                    _lastPix = p;
                }
                else
                {
                    DrawSegment(_lastPix, p, brushRadiusPx, penColor);
                    _lastPix = p;
                }
                _tex.Apply(false, false);
            }
        }

        if (Input.GetMouseButtonUp(0)) { _isDrawing = false; _hasLast = false; }
    }

    void TogglePanel() => paintArea.SetActive(!paintArea.activeSelf);

    void CreateSprite()
    {
        if (!_tex) return;
        
        var copy = new Texture2D(_tex.width, _tex.height, _tex.format, false);
        copy.SetPixels32(_tex.GetPixels32());
        copy.Apply(false, false);

        var sprite = Sprite.Create(copy,
                                   new Rect(0, 0, copy.width, copy.height),
                                   new Vector2(0.5f, 0.5f),
                                   pixelsPerUnit);

        OnSpriteCreated?.Invoke(sprite);
        SpriteFactory.Create(sprite, Vector3.zero, null, false, 3);
    }

    // --- drawing ---

    bool TryScreenToPixel(Vector3 screen, out Vector2Int pix)
    {
        pix = default;
        var canvas = sketchArea.GetComponentInParent<Canvas>();
        Camera cam = null;
        if (canvas && (canvas.renderMode == RenderMode.ScreenSpaceCamera || canvas.renderMode == RenderMode.WorldSpace))
            cam = canvas.worldCamera;

        if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(sketchArea, screen, cam, out var local))
            return false;

        // local is centered at (0,0) in rect; convert to [0,1]
        var rect = sketchArea.rect;
        float u = (local.x + rect.width * 0.5f) / rect.width;
        float v = (local.y + rect.height * 0.5f) / rect.height;
        if (u < 0f || u > 1f || v < 0f || v > 1f) return false;

        // If RawImage has Preserve Aspect ON, turn it OFF to keep this mapping 1:1.
        int x = Mathf.FloorToInt(u * (texWidth  - 1));
        int y = Mathf.FloorToInt(v * (texHeight - 1));
        pix = new Vector2Int(x, y);
        return true;
    }

    void StampDisc(int cx, int cy, int r, Color32 col)
    {
        int r2 = r * r;
        int xmin = Mathf.Max(0, cx - r);
        int xmax = Mathf.Min(texWidth - 1,  cx + r);
        int ymin = Mathf.Max(0, cy - r);
        int ymax = Mathf.Min(texHeight - 1, cy + r);

        for (int y = ymin; y <= ymax; y++)
        {
            int dy = y - cy;
            for (int x = xmin; x <= xmax; x++)
            {
                int dx = x - cx;
                if (dx * dx + dy * dy > r2) continue;
                _tex.SetPixel(x, y, col);
            }
        }
    }

    void DrawSegment(Vector2Int a, Vector2Int b, int r, Color32 col)
    {
        float dist = Vector2Int.Distance(a, b);
        if (dist < 1e-3f) { StampDisc(a.x, a.y, r, col); return; }
        int steps = Mathf.Max(1, Mathf.CeilToInt(dist / Mathf.Max(1f, r * 0.5f)));
        for (int i = 0; i <= steps; i++)
        {
            float t = i / (float)steps;
            int x = Mathf.RoundToInt(Mathf.Lerp(a.x, b.x, t));
            int y = Mathf.RoundToInt(Mathf.Lerp(a.y, b.y, t));
            StampDisc(x, y, r, col);
        }
    }

    bool IsMouseOverSketchArea(RectTransform rt)
    {
        var canvas = rt.GetComponentInParent<Canvas>();
        Camera cam = null;
        if (canvas && (canvas.renderMode == RenderMode.ScreenSpaceCamera || canvas.renderMode == RenderMode.WorldSpace))
            cam = canvas.worldCamera;
        return RectTransformUtility.RectangleContainsScreenPoint(rt, Input.mousePosition, cam);
    }
    
    private void Clean()
    {
        if (_tex == null) return;

        var px = new Color32[_tex.width * _tex.height];
        for (int i = 0; i < px.Length; i++) 
            px[i] = background;  // whatever background color you defined

        _tex.SetPixels32(px);
        _tex.Apply(false, false);
    }
}
