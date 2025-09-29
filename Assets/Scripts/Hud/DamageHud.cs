using System.Collections.Generic;
using UnityEngine;

public class DamageHud : MonoBehaviour
{
    [SerializeField] DamageText _textPrefab;         // prefab with TMP_Text

    [Header("Pool")]
    [SerializeField] int warmup = 16;                 // pre-spawn
    [SerializeField] int maxActive = 0;               // 0 = unlimited; >0 = cap and reuse oldest
    [SerializeField] Canvas canvas;  

    readonly Queue<DamageText> pool = new();
    readonly LinkedList<DamageText> active = new();  // for O(1) add/remove and "oldest" reuse

    void Awake()
    {
        App.Instance.Hud.DamageHud = this;

        for (int i = 0; i < warmup; i++)
            pool.Enqueue(Instantiate(_textPrefab, transform));
        foreach (var damageText in pool)
        {
            damageText.gameObject.SetActive(false);
        }
    }

    DamageText Get()
    {
        if (pool.Count > 0) return pool.Dequeue();

        // auto-grow
        return Instantiate(_textPrefab, transform);
    }

    void Recycle(DamageText p)
    {
        p.gameObject.SetActive(false);
        p.IsActive = false;
        p.Node = null;
        pool.Enqueue(p);
    }

    public void ShowDamage(Vector3 worldPos, float amount, float duration = 1f, float rise = 1.0f)
    {
        // Cap: reuse oldest if requested
        if (maxActive > 0 && active.Count >= maxActive)
        {
            var oldest = active.First.Value;
            Recycle(oldest);
            active.RemoveFirst();
        }

        var p = Get();
        p.gameObject.SetActive(true);

        // init
        p.Init(worldPos, amount, Mathf.Max(0.01f, duration), rise);

        // track
        p.Node = active.AddLast(p);
        p.IsActive = true;
    }

    private void Update()
    {
        if (active.Count == 0) return;

        float dt = Time.deltaTime;
        var node = active.First;
        while (node != null)
        {
            var next = node.Next; // cache: node may be removed
            var p = node.Value;

            p.t += dt;
            float u = p.t / p.life;
            if (u >= 1f)
            {
                // done
                active.Remove(node);
                Recycle(p);
            }
            else
            {
                float eased = 1f - Mathf.Pow(1f - u, 3f);
                Vector3 wpos = Vector3.Lerp(p.worldStart, p.worldEnd, eased) + p.offset;

                // ---- World -> Canvas conversion ----
                var rt = (RectTransform)p.transform;
                Vector2 sp = Camera.main.WorldToScreenPoint(wpos);
                RectTransformUtility.ScreenPointToLocalPointInRectangle(
                    (RectTransform)canvas.transform, sp, null, out var lp);
                rt.anchoredPosition = lp;
            }
            node = next;
        }
    }
}
