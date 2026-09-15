using System.Collections.Generic;
using UnityEngine;

namespace Binny
{
    /// <summary>
    /// Binny, the flying bin. Put him anywhere in a scene and he hangs there, bobbing on his
    /// thrusters. Press the call key and he finds his way to the player, parks at arm's length and
    /// hangs there instead. That is the whole of it for now — the recycling, the talking and the
    /// emotes all hook onto the same object later.
    ///
    /// He goes round things rather than through them: every trip is a route out of
    /// <see cref="BinnyPathfinder"/>, planned for his whole hull and re-planned a few times a
    /// second, because the player is walking and the world is destructible. If there is no way to
    /// where he was sent, he flies as far along as he can and comes to a stop at the obstruction
    /// instead of leaning on it — a bin that bulldozes the level while crossing it is doing the
    /// physics a favour nobody asked for.
    ///
    /// He is kinematic on purpose: he holds the station he is given rather than being knocked
    /// about by what he is carrying past. The bob is moved through the body rather than faked on
    /// the art, so the hull is always where the art is — whatever gets thrown into him later hits
    /// the thing you can see.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class BinnyController : MonoBehaviour
    {
        private enum State { Parked, Flying }

        [Header("Refs")]
        [SerializeField] private Rigidbody2D _rb;
        [SerializeField] private BinnyView _view;
        [Tooltip("The hull the route is planned for. Its size is the room he needs to get through a gap.")]
        [SerializeField] private Collider2D _shape;

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
                 "from, Y up. High enough that his hull clears the ground the player is standing " +
                 "on, or the spot he was sent to would be inside it and he could never reach it.")]
        [SerializeField] private Vector2 _standoff = new(2f, 1.6f);

        [Header("Route")]
        [Tooltip("What he has to fly round rather than through. Leave the player and the enemies " +
                 "out of it: he is on his way to one and should not be stopped by the other.")]
        [SerializeField] private LayerMask _obstacles = 1;
        [Tooltip("Grid step the route is searched on. Finer threads tighter gaps and costs more.")]
        [SerializeField] private float _cellSize = 0.5f;
        [Tooltip("Room he wants around the hull on top of its own size, so he clears a corner " +
                 "instead of grazing it. Covers the bob as well.")]
        [SerializeField] private float _skin = 0.1f;
        [Tooltip("How far he will look for a way round before settling for as close as he can get.")]
        [SerializeField] private float _searchRange = 30f;
        [Tooltip("Cells the search may open per attempt. The ceiling on what one trip costs.")]
        [SerializeField] private int _searchBudget = 800;
        [Tooltip("Seconds between re-plans while flying — the player moves and the ground changes.")]
        [SerializeField] private float _replanInterval = 0.35f;

        [Header("Hover")]
        [Tooltip("Height of the idle bob.")]
        [SerializeField] private float _bobHeight = 0.12f;
        [Tooltip("Seconds for one bob.")]
        [SerializeField] private float _bobPeriod = 2.4f;
        [Tooltip("Sideways drift on top of the bob, at half its rate so the two never trace a circle.")]
        [SerializeField] private float _swayWidth = 0.06f;

        [Header("Faces")]
        [Tooltip("How long he reacts to the trip after landing it — pleased if he got there, " +
                 "put out if the way was blocked.")]
        [SerializeField] private float _arrivalFace = 1.1f;

        [Header("Debug")]
        [Tooltip("Draw the route in the scene view while he flies it — legs, waypoints, the room " +
                 "the search kept clear for him, and where he expects to come to a stop.")]
        [SerializeField] private bool _drawRoute = true;

        private State _state = State.Parked;

        // Where he holds station, and where the chassis is before the hover wobble is added on.
        // Keeping the two apart is what stops the bob from walking him across the room.
        private Vector2 _anchor;
        private Vector2 _chassis;
        private Vector2 _velocity;

        private bool _chasePlayer;
        private Vector2 _destination;
        private float _parkSide = 1f;

        private BinnyPathfinder _finder;
        private readonly List<Vector2> _path = new();
        private int _leg;
        private bool _routeComplete = true;
        private float _replanAt;

        private float _bobPhase;
        private float _faceUntil;
        private bool _pleased;
        private bool _lostPlayer;

        /// <summary>True while he is holding station rather than going somewhere.</summary>
        public bool IsParked => _state == State.Parked;

        /// <summary>The spot he is holding, wobble not included.</summary>
        public Vector2 Station => _anchor;

        /// <summary>False if the last trip ended at an obstruction rather than where he was sent.</summary>
        public bool ReachedStation => _routeComplete;

        private void Reset()
        {
            _rb = GetComponent<Rigidbody2D>();
            _view = GetComponentInChildren<BinnyView>();
            _shape = GetComponent<Collider2D>();
        }

        private void Awake()
        {
            if (!_rb) _rb = GetComponent<Rigidbody2D>();
            if (!_view) _view = GetComponentInChildren<BinnyView>();
            if (!_shape) _shape = GetComponent<Collider2D>();

            _chassis = _rb.position;
            _anchor = _chassis;

            _finder = new BinnyPathfinder(_cellSize, Clearance(), _obstacles, _searchBudget, _searchRange, transform);

            // Two of them in one scene should not bob in lockstep.
            _bobPhase = Random.value * _bobPeriod;
        }

        /// <summary>
        /// The box that has to be empty for him to be somewhere: his own hull, plus a skin, plus
        /// the bob — he is never exactly on his station, so the route has to allow for the wobble
        /// or he clips the ceiling of a gap he technically fits through.
        /// </summary>
        private Vector2 Clearance()
        {
            var hull = _shape ? (Vector2)_shape.bounds.size : Vector2.zero;

            // A collider that has not been through a physics step yet can measure nothing. Better
            // a guess at his own size than a route planned for a point, which fits anywhere.
            if (hull.x < 0.01f || hull.y < 0.01f) hull = Vector2.one * 2f;

            return hull + new Vector2(_skin + Mathf.Abs(_swayWidth), _skin + Mathf.Abs(_bobHeight)) * 2f;
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
            Depart();
        }

        /// <summary>Go and hang there instead. For whatever ends up wanting him somewhere specific.</summary>
        public void SendTo(Vector2 point)
        {
            _chasePlayer = false;
            _destination = point;
            Depart();
        }

        /// <summary>Stop where he is, right now.</summary>
        public void Halt()
        {
            _anchor = _chassis;
            _velocity = Vector2.zero;
            _state = State.Parked;

            // The route is left in place rather than dropped: he is finished with it, but it is
            // the record of the trip he just made, and it is still on screen to be read.
            _leg = _path.Count;
        }

        private void Depart()
        {
            _state = State.Flying;
            _replanAt = 0f; // plan on the next step rather than waiting out the interval
        }

        /// <summary>
        /// Follow the route, re-planning it on a timer. Only the end of the route is braked for:
        /// the corners are legs of one flight, not stops, so he carries his speed round them.
        /// </summary>
        private void Fly(float dt)
        {
            if (Time.time >= _replanAt) Plan();

            if (_leg >= _path.Count)
            {
                // Nowhere to go: either he is already there, or the way is blocked from the first
                // step. Either way this is where he stops.
                Arrive();
                return;
            }

            bool last = _leg == _path.Count - 1;
            Vector2 waypoint = _path[_leg];
            Vector2 to = waypoint - _chassis;
            float distance = to.magnitude;

            if (distance <= (last ? _arriveRadius : _cellSize * 0.75f))
            {
                _leg++;
                if (!last) return;

                _chassis = waypoint;
                Arrive();
                return;
            }

            float remaining = distance + LengthAfter(_leg);
            float wanted = Mathf.Min(_cruiseSpeed, Mathf.Sqrt(2f * _braking * remaining));
            Vector2 desired = to / distance * wanted;

            _velocity = Vector2.MoveTowards(_velocity, desired, _acceleration * dt);
            _chassis += _velocity * dt;
        }

        private void Hold(float dt)
        {
            _velocity = Vector2.MoveTowards(_velocity, Vector2.zero, _acceleration * dt);
            _chassis = _anchor;
        }

        private void Plan()
        {
            _replanAt = Time.time + _replanInterval;

            var goal = Target();
            bool exact = _finder.TryFind(_chassis, goal, _path);

            // A cell short of the spot is not worth sulking over: he is there as far as anyone
            // watching is concerned. Anything further and he really was stopped by something.
            _routeComplete = exact ||
                             (_path.Count > 0 && Vector2.Distance(_path[_path.Count - 1], goal) <= _cellSize * 1.5f);

            // The first point of a route is always where he already is.
            _leg = _path.Count > 1 ? 1 : _path.Count;
        }

        private void Arrive()
        {
            _pleased = _routeComplete;
            _faceUntil = Time.time + _arrivalFace;
            Halt();
        }

        /// <summary>What is left of the route past this leg, for working out when to brake.</summary>
        private float LengthAfter(int leg)
        {
            float total = 0f;
            for (int i = leg; i < _path.Count - 1; i++) total += Vector2.Distance(_path[i], _path[i + 1]);

            return total;
        }

        /// <summary>
        /// The moving spot beside the player, or the fixed one he was sent to. Re-reading it every
        /// plan is what makes him follow you round a corner on the way in, instead of flying at
        /// where you were standing when you whistled.
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
        /// Angry parked, startled in the air, and a moment of something on arrival: pleased if he
        /// got where he was going, sad if he is sitting against a wall instead.
        /// </summary>
        private BinnyFace WantedFace()
        {
            if (Time.time < _faceUntil) return _pleased ? BinnyFace.Happy : BinnyFace.Sad;

            return _state == State.Flying ? BinnyFace.Surprised : BinnyFace.Angry;
        }

        /// <summary>Idle wobble, added on top of the station he holds.</summary>
        private Vector2 Hover()
        {
            float t = _bobPhase * Mathf.PI * 2f / Mathf.Max(0.01f, _bobPeriod);

            return new Vector2(Mathf.Sin(t * 0.5f) * _swayWidth, Mathf.Sin(t) * _bobHeight);
        }

        // ------------------------------------------------------------------ gizmos

        private static readonly Color Flown = new(1f, 1f, 1f, 0.3f);
        private static readonly Color Ahead = new(1f, 0.55f, 0.2f, 0.95f);
        private static readonly Color Footprint = new(1f, 0.55f, 0.2f, 0.3f);
        private static readonly Color Reached = new(0.35f, 1f, 0.45f, 0.95f);
        private static readonly Color Blocked = new(1f, 0.3f, 0.25f, 0.95f);

        /// <summary>
        /// The route as it stands, drawn whether or not he is selected, because the thing you want
        /// to watch is a flight in progress: legs behind him in white, legs ahead in orange, a dot
        /// on the waypoint he is steering at, and the box that had to be clear for every cell of it
        /// — which is usually the whole answer to "why did he stop there".
        ///
        /// The end of the route is boxed green if it is where he was sent and red if it is as far
        /// as he could get, with the same word next to it.
        /// </summary>
        private void OnDrawGizmos()
        {
            if (!_drawRoute || !Application.isPlaying) return;

            var clearance = Clearance();

            Gizmos.color = Footprint;
            Gizmos.DrawWireCube(_chassis, clearance);

            if (_path.Count == 0) return;

            for (int i = 0; i < _path.Count - 1; i++) Leg(_path[i], _path[i + 1], i < _leg - 1 ? Flown : Ahead);

            for (int i = 1; i < _path.Count; i++)
            {
                Gizmos.color = i < _leg ? Flown : Ahead;
                Gizmos.DrawWireSphere(_path[i], _cellSize * 0.2f);
            }

            if (_leg < _path.Count)
            {
                Gizmos.color = Ahead;
                Gizmos.DrawSphere(_path[_leg], _cellSize * 0.3f);
            }

            var end = _path[_path.Count - 1];
            var verdict = _routeComplete ? Reached : Blocked;

            Gizmos.color = verdict;
            Gizmos.DrawWireCube(end, clearance);

#if UNITY_EDITOR
            UnityEditor.Handles.color = verdict;
            UnityEditor.Handles.Label(end + Vector2.up * (clearance.y * 0.5f + 0.25f),
                _routeComplete ? "Binny: station" : "Binny: blocked");
#endif
        }

        /// <summary>One leg of the route. Thick enough to see over the terrain where there is an editor to ask.</summary>
        private static void Leg(Vector2 from, Vector2 to, Color colour)
        {
#if UNITY_EDITOR
            UnityEditor.Handles.color = colour;
            UnityEditor.Handles.DrawAAPolyLine(4f, from, to);
#else
            Gizmos.color = colour;
            Gizmos.DrawLine(from, to);
#endif
        }

        private void OnDrawGizmosSelected()
        {
            // Where he is holding, which is not quite where he is: the bob is on top of it.
            Gizmos.color = new Color(0.78f, 0.27f, 0.16f, 0.8f);
            Gizmos.DrawWireSphere(Application.isPlaying ? (Vector3)_anchor : transform.position, _arriveRadius);
        }
    }
}
