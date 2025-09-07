using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class SpawnItemView : MonoBehaviour, IPointerClickHandler, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    public Action<SpawnItemView> OnClick;
    public Action<SpawnItemView> OnBeginDragEvent;
    public Action<SpawnItemView> OnEndDragEvent;

    [SerializeField] private Image _image;
    [SerializeField] private GameObject _selectedBg;

    public Sprite Sprite => _image.sprite;

    private RectTransform _ghost;
    private Canvas _rootCanvas;

    public void Init(Sprite image) => _image.sprite = image;
    public void Select(bool value) => _selectedBg.SetActive(value);

    public void OnPointerClick(PointerEventData eventData) => OnClick?.Invoke(this);

    public void OnBeginDrag(PointerEventData eventData)
    {
        if (_rootCanvas == null) _rootCanvas = GetComponentInParent<Canvas>().rootCanvas;

        var go = new GameObject("DragGhost", typeof(RectTransform), typeof(CanvasGroup), typeof(Image));
        _ghost = (RectTransform)go.transform;
        _ghost.SetParent(_rootCanvas.transform, false);
        _ghost.sizeDelta = ((RectTransform)transform).rect.size;
        _ghost.localScale = new Vector3(0.5f, 0.5f, 0.5f);

        go.GetComponent<Image>().enabled = false;

        var cg = go.GetComponent<CanvasGroup>();
        cg.blocksRaycasts = false;
        cg.alpha = 0.8f;

        _ghost.position = eventData.position;

        OnBeginDragEvent?.Invoke(this);
    }

    public void OnDrag(PointerEventData eventData)
    {
        if (_ghost) _ghost.position = eventData.position;
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        if (_ghost) Destroy(_ghost.gameObject);
        OnEndDragEvent?.Invoke(this);
    }
}