using UnityEngine;
using TMPro;
using System.Collections.Generic;

public class DamageText : MonoBehaviour
{
    [Header("Refs")] public TMP_Text label; // assign in prefab (set label.raycastTarget = false)

    [HideInInspector] public bool IsActive;
    [HideInInspector] public LinkedListNode<DamageText> Node;

    [HideInInspector] public Vector3 worldStart, worldEnd, offset;
    [HideInInspector] public float t, life;

    public void Init(Vector3 worldPos, float amount, float duration, float rise)
    {
        t = 0f;
        life = duration;

        label.text = Mathf.RoundToInt(amount).ToString();
        worldStart = worldPos;
        worldEnd = worldPos + Vector3.up * rise;

        transform.position = worldStart;
    }
}