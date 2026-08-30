using UnityEngine;

namespace Props
{
    /// <summary>
    /// Two keys on a winch, so a rig dropped in the scene works without writing anything.
    ///
    /// <see cref="Winch2D"/> takes its orders through <see cref="Winch2D.MotorInput"/> and does
    /// not care where they come from — a lever, a button, an enemy, this. Swap it out for
    /// whatever the level actually uses; nothing else depends on it being here.
    /// </summary>
    [RequireComponent(typeof(Winch2D))]
    [AddComponentMenu("PhysFun/Winch Input")]
    public sealed class WinchInput2D : MonoBehaviour
    {
        [SerializeField] private KeyCode haulKey = KeyCode.E;
        [SerializeField] private KeyCode payOutKey = KeyCode.Q;

        [Tooltip("Only reachable from this close to the winch. 0 = always reachable.")]
        [SerializeField, Min(0f)] private float range;
        [Tooltip("Who has to be in range. Falls back to whatever is tagged Player.")]
        [SerializeField] private Transform user;

        private Winch2D _winch;

        private void Awake()
        {
            _winch = GetComponent<Winch2D>();
            if (!user && range > 0f)
            {
                var player = GameObject.FindGameObjectWithTag("Player");
                if (player) user = player.transform;
            }
        }

        private void Update()
        {
            if (!InReach()) { _winch.MotorInput = 0f; return; }

            float input = 0f;
            if (Input.GetKey(haulKey)) input += 1f;
            if (Input.GetKey(payOutKey)) input -= 1f;
            _winch.MotorInput = input;
        }

        private bool InReach() =>
            range <= 0f || (user && Vector2.Distance(user.position, transform.position) <= range);
    }
}
