using System.Collections.Generic;
using System.Linq;
using Spawners;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class ObjectSpawner : MonoBehaviour
{
    [SerializeField] private Button _spawnButton;
    [SerializeField] private Slider _slider;
    [SerializeField] private TextMeshProUGUI _lodText;
    [SerializeField] private SpawnItemView _spawnPrefab;
    [SerializeField] private Transform _content;

    private List<SpawnItemView> _views = new();
    private SpawnItemView _currentView;

    private GameObject _preview;
    private float _angleDeg;

    private void Start()
    {
        var sprites = Resources.LoadAll<Sprite>("SpawnImages").ToList();
        _lodText.text = $"Simplification level {_slider.value}";

        foreach (var s in sprites)
        {
            var v = Instantiate(_spawnPrefab, _content);
            v.Init(s);
            v.OnClick += OnItemSelected;
            v.OnBeginDragEvent += BeginPreviewFromItem;
            v.OnEndDragEvent += EndPreviewFromItem;
            _views.Add(v);
        }
    }

    private void OnEnable()
    {
        _spawnButton.onClick.AddListener(SpawnCurrent);
        _slider.onValueChanged.AddListener(ChangeLod);
    }

    private void OnDisable()
    {
        _spawnButton.onClick.RemoveListener(SpawnCurrent);
        _slider.onValueChanged.RemoveListener(ChangeLod);
    }

    private void Update()
    {
        if (_preview == null) return;

        // move preview with mouse
        var pos = MouseWorld();
        _preview.transform.position = pos;

        // rotate with wheel
        float delta = Input.mouseScrollDelta.y;
        if (Mathf.Abs(delta) > 0.0001f)
        {
            _angleDeg += delta * 15f; // step per tick
            _preview.transform.rotation = Quaternion.Euler(0f, 0f, _angleDeg);
        }
    }

    private void BeginPreviewFromItem(SpawnItemView item)
    {
        _currentView = item;
        _angleDeg = 0f;

        // make a semi-transparent preview
        _preview = SpriteFactory.Create(item.Sprite, MouseWorld(), null, false, (int)_slider.value);
        var sr = _preview.GetComponent<SpriteRenderer>();
        var c = sr.color; c.a = 0.7f; sr.color = c;
        var rb = _preview.GetComponent<Rigidbody2D>(); if (rb) rb.simulated = false; // no physics during preview
    }

    private void EndPreviewFromItem(SpawnItemView item)
    {
        if (_preview == null) return;

        // finalize: make fully opaque + enable physics
        var sr = _preview.GetComponent<SpriteRenderer>();
        var c = sr.color; c.a = 1f; sr.color = c;

        var rb = _preview.GetComponent<Rigidbody2D>(); if (rb) rb.simulated = true;

        _preview = null; // keep spawned object in scene
    }

    private void SpawnCurrent()
    {
        if (_currentView == null) return;
        SpriteFactory.Create(_currentView.Sprite, Vector3.zero, null, false, (int)_slider.value);
    }

    private void OnItemSelected(SpawnItemView selected)
    {
        _currentView?.Select(false);
        selected.Select(true);
        _currentView = selected;
    }

    private void ChangeLod(float value) => _lodText.text = $"Simplification level {_slider.value}";

    private static Vector3 MouseWorld()
    {
        var cam = Camera.main;
        var sp = Input.mousePosition;
        sp.z = -cam.transform.position.z; // distance to Z=0 plane
        var wp = cam.ScreenToWorldPoint(sp);
        wp.z = 0f;
        return wp;
    }
}