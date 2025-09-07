using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class SpawnItemView : MonoBehaviour, IPointerClickHandler
{
    public Action<SpawnItemView> OnClick;

    [SerializeField] private Image _image;
    [SerializeField] private GameObject _selectedBg;

    public Sprite Sprite => _image.sprite;

    public void Init(Sprite image)
    {
        _image.sprite = image;
    }

    public void Select(bool value)
    {
        _selectedBg.SetActive(value);
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        Debug.Log("Image clicked: " + gameObject.name);
        OnClick?.Invoke(this);
    }
}
