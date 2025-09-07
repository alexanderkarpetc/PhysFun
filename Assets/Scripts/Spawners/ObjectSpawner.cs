using System;
using System.Collections.Generic;
using System.Linq;
using Spawners;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using Button = UnityEngine.UI.Button;

public class ObjectSpawner : MonoBehaviour
{
    [SerializeField] private Button _spawnButton;
    [SerializeField] private Slider _slider;
    [SerializeField] private TextMeshProUGUI _lodText;
    [SerializeField] private SpawnItemView _spawnPrefab;
    [SerializeField] private Transform _content;

    private List<SpawnItemView> _views = new();
    private SpawnItemView _currentView;

    private void Start()
    {
        var sprites = Resources.LoadAll<Sprite>("Sprites").ToList();
        _lodText.text = $"Simplification level {_slider.value}";
        sprites.ForEach(x =>
        {
            var itemView = Instantiate(_spawnPrefab, _content);
            itemView.Init(x);
            itemView.OnClick += OnItemSelected;
            _views.Add(itemView);
        });
    }

    private void OnEnable()
    {
        _spawnButton.onClick.AddListener(Spawn);
        _slider.onValueChanged.AddListener(ChangeLod);
    }

    private void OnDisable()
    {
        _spawnButton.onClick.RemoveListener(Spawn);
        _slider.onValueChanged.RemoveListener(ChangeLod);
    }

    private void Spawn()
    {
        if (_currentView == null)
            return;
        
        SpriteFactory.Create(_currentView.Sprite, new Vector3(), null, false, (int)_slider.value);
    }
    
    private void OnItemSelected(SpawnItemView selectedItem)
    {
        _currentView?.Select(false);
        selectedItem.Select(true);
        _currentView = selectedItem;
    }
    
    private void ChangeLod(float value)
    {
        _lodText.text = $"Simplification level {_slider.value}";
    }
}
