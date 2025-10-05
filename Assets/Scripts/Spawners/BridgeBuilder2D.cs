using UnityEngine;
#if UNITY_EDITOR
using UnityEditor;
#endif

public class BridgeBuilder2D : MonoBehaviour
{
    [Header("Anchors (ends of the bridge)")]
    public Transform leftAnchor;
    public Transform rightAnchor;

    [Header("Segment prefab (must have Rigidbody2D + Collider2D)")]
    public GameObject segmentPrefab;

    [Header("Layout")]
    [Min(2)] public int segmentCount = 12;
    public bool autoSegmentLength = true;
    [Min(0.01f)] public float segmentLength = 1.0f; // used if autoSegmentLength=false

    [Header("Hinge setup")]
    public Vector2 localAnchorA = new Vector2(-0.5f, 0f); // левый край
    public Vector2 localAnchorB = new Vector2( 0.5f, 0f); // правый край
    // public bool enableLimits = false;
    // public float minAngle = -25f;
    // public float maxAngle = 25f;
    public bool enableBreak = false;
    public int breakForce = 20000;

    [Header("Edge attachment")]
    public bool attachToWorldIfNoRB = true; // если у опоры нет Rigidbody2D
    public bool useFixedOnEnds = false;     // иначе используем Hinge на концах

    [Header("Stabilizers (optional cables)")]
    public bool useStabilizers = false;
    [Min(0f)] public float stabilizerHeight = 2.5f; // точка крепления над сегментом
    [Range(1, 8)] public int stabilizerEvery = 2;    // через сколько сегментов ставить
    [Min(0.1f)] public float stabilizerSlack = 0.2f; // длина > вертикали, для лёгкого провиса

    [Header("Generated")]
    public Transform segmentsRoot;

    private void Reset()
    {
        // Попытка авто-настроить якоря по ширине объекта
        if (!leftAnchor)
        {
            var l = new GameObject("LeftAnchor").transform;
            l.SetParent(transform);
            l.localPosition = Vector3.left * 5f;
            leftAnchor = l;
        }
        if (!rightAnchor)
        {
            var r = new GameObject("RightAnchor").transform;
            r.SetParent(transform);
            r.localPosition = Vector3.right * 5f;
            rightAnchor = r;
        }
    }

#if UNITY_EDITOR
    [ContextMenu("Rebuild Bridge")]
    public void EditorRebuild() { Build(true); }
#endif

    public void Build(bool inEditor = false)
    {
        if (!leftAnchor || !rightAnchor || !segmentPrefab)
        {
            Debug.LogError("[BridgeBuilder2D] Missing references.");
            return;
        }

        // Удаляем предыдущие сегменты 
        if (segmentsRoot != null)
        {
#if UNITY_EDITOR
            if (inEditor)
                DestroyImmediate(segmentsRoot.gameObject);
            else
#endif
                Destroy(segmentsRoot.gameObject);
        }

        segmentsRoot = new GameObject("BridgeSegments").transform;
        segmentsRoot.SetParent(transform, worldPositionStays:false);

        Vector2 A = leftAnchor.position;
        Vector2 B = rightAnchor.position;
        Vector2 dir = (B - A);
        float totalLen = dir.magnitude;
        Vector2 dirN = dir.normalized;

        float segLen = autoSegmentLength ? (totalLen / segmentCount) : segmentLength;

        Rigidbody2D[] rbs = new Rigidbody2D[segmentCount];

        // Создаём сегменты по прямой — физика сама “повесит”
        Vector2 start = A;
        for (int i = 0; i < segmentCount; i++)
        {
            Vector2 pos = start + dirN * (segLen * (i + 0.5f));
            var go = Instantiate(segmentPrefab, pos, Quaternion.FromToRotation(Vector3.right, dirN), segmentsRoot);
            var rb = go.GetComponent<Rigidbody2D>();
            if (!rb)
            {
                Debug.LogError("segmentPrefab must contain Rigidbody2D.");
                return;
            }
            rbs[i] = rb;
        }

        // Соединяем Hinge между соседями
        for (int i = 0; i < segmentCount - 1; i++)
        {
            CreateHinge(rbs[i], rbs[i + 1], localAnchorB, localAnchorA, enableBreak, breakForce);
        }

        // Крепим края к опорам
        Rigidbody2D leftRB  = leftAnchor.GetComponent<Rigidbody2D>();
        Rigidbody2D rightRB = rightAnchor.GetComponent<Rigidbody2D>();

        if (useFixedOnEnds)
        {
            CreateFixed(rbs[0],     leftRB,  leftAnchor.position);
            CreateFixed(rbs[^1],    rightRB, rightAnchor.position);
        }
        else
        {
            CreateHingeToAnchor(rbs[0],  leftRB,  leftAnchor.position, localAnchorA);
            CreateHingeToAnchor(rbs[^1], rightRB, rightAnchor.position, localAnchorB);
        }

        // Стабилизаторы (тросы) вверх
        if (useStabilizers)
        {
            for (int i = 0; i < segmentCount; i += stabilizerEvery)
            {
                var rb = rbs[i];
                Vector2 top = (Vector2)rb.worldCenterOfMass + Vector2.up * stabilizerHeight;

                var dj = rb.gameObject.AddComponent<DistanceJoint2D>();
                dj.autoConfigureDistance = false;
                dj.connectedBody = null; // к миру
                dj.connectedAnchor = top;
                float d = Vector2.Distance(rb.worldCenterOfMass, top);
                dj.distance = d + stabilizerSlack;
                dj.maxDistanceOnly = false;
                dj.enableCollision = false;
            }
        }
    }

    private static HingeJoint2D CreateHinge(Rigidbody2D a, Rigidbody2D b,
        Vector2 anchorLocalA, Vector2 anchorLocalB, bool useBreak = false, int breakForce = 20000)
    {
        var hj = a.gameObject.AddComponent<HingeJoint2D>();
        hj.autoConfigureConnectedAnchor = false;
        hj.connectedBody = b;
        hj.anchor = anchorLocalA;
        hj.connectedAnchor = anchorLocalB;
        hj.enableCollision = false;

        // if (limits)
        // {
        //     var lim = new JointAngleLimits2D
        //     {
        //         min = min,
        //         max = max
        //     };
        //     hj.limits = lim;
        //     hj.useLimits = true;
        // }
        if (useBreak)
        {
            hj.breakForce = breakForce;
        }

        return hj;
    }

    private void CreateHingeToAnchor(Rigidbody2D seg, Rigidbody2D anchorRB, Vector2 worldAnchor, Vector2 segLocalAnchor)
    {
        var hj = seg.gameObject.AddComponent<HingeJoint2D>();
        hj.autoConfigureConnectedAnchor = false;
        hj.anchor = segLocalAnchor;

        if (anchorRB != null)
        {
            hj.connectedBody = anchorRB;
            // connectedAnchor в лок.координатах anchorRB
            Vector2 local = anchorRB.transform.InverseTransformPoint(worldAnchor);
            hj.connectedAnchor = local;
        }
        else
        {
            // Крепим к миру в точке worldAnchor
            hj.connectedBody = null;
            hj.connectedAnchor = worldAnchor;
        }
        //
        // if (enableLimits)
        // {
        //     hj.useLimits = true;
        //     hj.limits = new JointAngleLimits2D { min = minAngle, max = maxAngle };
        // }
    }

    private static FixedJoint2D CreateFixed(Rigidbody2D seg, Rigidbody2D anchorRB, Vector2 worldAnchor)
    {
        var fj = seg.gameObject.AddComponent<FixedJoint2D>();
        fj.autoConfigureConnectedAnchor = false;

        if (anchorRB != null)
        {
            fj.connectedBody = anchorRB;
            fj.connectedAnchor = anchorRB.transform.InverseTransformPoint(worldAnchor);
        }
        else
        {
            fj.connectedBody = null;     // к миру
            fj.connectedAnchor = worldAnchor;
        }
        fj.enableCollision = false;
        return fj;
    }

#if UNITY_EDITOR
    private void OnDrawGizmosSelected()
    {
        if (!leftAnchor || !rightAnchor) return;
        Gizmos.color = Color.gray;
        Gizmos.DrawLine(leftAnchor.position, rightAnchor.position);

        if (useStabilizers && segmentsRoot)
        {
            Gizmos.color = Color.white;
            foreach (Transform t in segmentsRoot)
            {
                var rb = t.GetComponent<Rigidbody2D>();
                if (!rb) continue;
                Vector2 top = (Vector2)rb.worldCenterOfMass + Vector2.up * stabilizerHeight;
                Gizmos.DrawLine(rb.worldCenterOfMass, top);
            }
        }
    }
#endif
}
