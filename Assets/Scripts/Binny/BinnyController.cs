using UnityEngine;

namespace Binny
{
    /// <summary>
    /// Binny, the flying bin. Put him anywhere in a scene and he hangs there, bobbing on his
    /// thrusters. Press the call key and he flies over to the player, parks at arm's length and
    /// hangs there instead. That is the whole of it for now — the recycling, the talking and the
    /// emotes all hook onto the same object later.
    ///
    /// He is kinematic on purpose: he holds the station he is given and shoves debris out of the
    /// way rather than being knocked about by it, which is what a hovering machine should feel
    /// like and what makes "stop here" mean it. The bob is moved through the body rather than
    /// faked on the art, so the hull is always where the art is — whatever gets thrown into him
    /// later hits the thing you can see.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class BinnyController : MonoBehaviour
    {
        private enum State { Parked, Flying }

        [Header("Refs")]
        [SerializeField] private Rigidbody2D _rb;
        [SerializeField] private BinnyView _view;

        [Header("Call")]
        [Tooltip("Press to send him to the player. He stays where he lands.")]
        [SerializeField] private KeyCode _callKey = KeyCode.B;

        [Header("Flight")]
        [Tooltip("Top speed, world units per second.")]
        [SerializeField] private float _cruiseSpeed = 7f;
        [Tooltip("How hard he can change his mind. Low numbers make him drift through the turns.")]
        [SerializeField] private float _acceleration = 22f;
        [Tooltip("Deceleration he plans the arrival around: he eases off far enough out to stop " +
                 "dead on the spot instead of sailing past it.")]
        [SerializeField] private float _braking = 26f;
        [Tooltip("Close enough. Anything tighter and he hunts around the spot forever.")]
        [SerializeField] private float _arriveRadius = 0.15f;

        [Header("Where he parks")]
        [Tooltip("Offset from the player he comes to rest at: X out to the side he approached " +
                 "from, Y up. Far enough not to be in the way, close enough to be yours.")]
        [SerializeField] private Vector2 _standoff = new(2f, 1.2f);

        [Header("Hover")]
        [Tooltip("Height of the idle bob.")]
        [SerializeField] private float _bobHeight = 0.12f;
        [Tooltip("Seconds for one bob.")]
        [SerializeField] private float _bobPeriod = 2.4f;
        [Tooltip("Sideways drift on top of the bob, at half its rate so the two never trace a circle.")]
        [SerializeField] private float _swayWidth = 0.06f;

        [Header("Faces")]
        [Tooltip("How long he looks pleased with himself after landing the trip.")]
        [SerializeField] private float _arrivalCheer = 1.1f;

        private State _state = State.Parked;

        // Where he holds station, and where the chassis is before the hover wobble is added on.
        // Keeping the two apart is what stops the bob from walking him across the room.
        private Vector2 _anchor;
        private Vector2 _chassis;
        private Vector2 _velocity;

        private bool _chasePlayer;
        private Vector2 _destination;
        private float _parkSide = 1f;

        private float _bobPhase;
        private float _cheerUntil;
        private bool _lostPlayer;

        /// <summary>True while he is holding station rather than going somewhere.</summary>
        public bool IsParked => _state == State.Parked;

        /// <summary>The spot he is holding, wobble not included.</summary>
        public Vector2 Station => _anchor;

        private void Reset()
        {
            _rb = GetComponent<Rigidbody2D>();
            _view = GetComponentInChildren<BinnyView>();
        }

        private void Awake()
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
            if (!_view) _view = GetComponentInChildren<BinnyView>();

            _chassis = _rb.position;
            _anchor = _chassis;

            // Two of them in one scene should not bob in lockstep.
            _bobPhase = Random.value * _bobPeriod;
        }

        private void Update()
        {
            if (Input.GetKeyDown(_callKey)) Call();
        }

        private void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;

            if (_state == State.Flying) Fly(dt);
            else Hold(dt);

            _bobPhase += dt;
            _rb.MovePosition(_chassis + Hover());

            if (!_view) return;

            _view.SetMotion(_velocity);
            _view.SetThrust(_state == State.Flying);
            _view.SetFace(WantedFace());
        }

        /// <summary>
        /// Come here. Which side of the player he parks on is settled once, at the moment he is
        /// called — the side he is already on — so that crossing over mid-flight does not make him
        /// change his mind about where he is going.
        /// </summary>
        public void Call()
        {
            var player = App.Instance.PlayerTransform;
            if (!player)
            {
                if (!_lostPlayer)
                {
                    Debug.LogWarning("[Binny] Called, but there is no player in the scene to fly to.", this);
                    _lostPlayer = true;
                }

                return;
            }

            _parkSide = _chassis.x >= player.position.x ? 1f : -1f;
            _chasePlayer = true;
            _state = State.Flying;
        }

        /// <summary>Go and hang there instead. For whatever ends up wanting him somewhere specific.</summary>
        public void SendTo(Vector2 point)
        {
            _chasePlayer = false;
            _destination = point;
            _state = State.Flying;
        }

        /// <summary>Stop where he is, right now.</summary>
        public void Halt()
        {
            _anchor = _chassis;
            _velocity = Vector2.zero;
            _state = State.Parked;
        }

        /// <summary>
        /// Steer at the target and arrive on it. The wanted speed is whatever he could still brake
        /// down from over the distance left, capped at cruise, so the approach eases itself off
        /// without any special "slowing down now" case.
        /// </summary>
        private void Fly(float dt)
        {
            Vector2 target = Target();
            Vector2 to = target - _chassis;
            float distance = to.magnitude;

            if (distance <= _arriveRadius)
            {
                _chassis = target;
                _cheerUntil = Time.time + _arrivalCheer;
                Halt();
                return;
            }

            float wanted = Mathf.Min(_cruiseSpeed, Mathf.Sqrt(2f * _braking * distance));
            Vector2 desired = to / distance * wanted;

            _velocity = Vector2.MoveTowards(_velocity, desired, _acceleration * dt);
            _chassis += _velocity * dt;
        }

        private void Hold(float dt)
        {
            _velocity = Vector2.MoveTowards(_velocity, Vector2.zero, _acceleration * dt);
            _chassis = _anchor;
        }

        /// <summary>
        /// The moving spot beside the player, or the fixed one he was sent to. Chasing it live is
        /// what makes him follow you round a corner on the way in, instead of flying at where you
        /// were standing when you whistled.
        /// </summary>
        private Vector2 Target()
        {
            if (!_chasePlayer) return _destination;

            var player = App.Instance.PlayerTransform;
            if (!player)
            {
                // Player gone mid-flight (a reload, a death). Settle rather than fly at the origin.
                Halt();
                return _chassis;
            }

            return (Vector2)player.position + new Vector2(_parkSide * _standoff.x, _standoff.y);
        }

        /// <summary>
        /// Angry parked, startled in the air, pleased with himself for a moment on arrival — the
        /// reading the concept sheet asks for.
        /// </summary>
        private BinnyFace WantedFace()
        {
            if (Time.time < _cheerUntil) return BinnyFace.Happy;

            return _state == State.Flying ? BinnyFace.Surprised : BinnyFace.Angry;
        }

        /// <summary>Idle wobble, added on top of the station he holds.</summary>
        private Vector2 Hover()
        {
            float t = _bobPhase * Mathf.PI * 2f / Mathf.Max(0.01f, _bobPeriod);

            return new Vector2(Mathf.Sin(t * 0.5f) * _swayWidth, Mathf.Sin(t) * _bobHeight);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.78f, 0.27f, 0.16f, 0.8f);
            Gizmos.DrawWireSphere(Application.isPlaying ? (Vector3)_anchor : transform.position, _arriveRadius);
        }
    }
}
