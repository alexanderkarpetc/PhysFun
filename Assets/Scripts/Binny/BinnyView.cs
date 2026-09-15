using UnityEngine;

namespace Binny
{
    /// <summary>
    /// The art and nothing else: gears that turn with the travel, thrusters that burn only while
    /// he is going somewhere, a screen that shows whatever face it is handed, and a lean into the
    /// direction of flight. It decides nothing — <see cref="BinnyController"/> pushes the state in
    /// every physics step and this reads it back out at frame rate.
    ///
    /// Everything is drawn from the loose parts in <c>GameConcepts/Binny</c>, laid out in the
    /// order the README gives: thrust, body, gears, face. The BinnyBuilder menu item is what
    /// wires the renderers and the sprite lists; nothing here is meant to be filled in by hand.
    /// </summary>
    public sealed class BinnyView : MonoBehaviour
    {
        [Header("Renderers")]
        [SerializeField] private SpriteRenderer _face;
        [SerializeField] private SpriteRenderer _gearLeft;
        [SerializeField] private SpriteRenderer _gearRight;
        [SerializeField] private SpriteRenderer _thrustLeft;
        [SerializeField] private SpriteRenderer _thrustRight;

        [Header("Sprites")]
        [Tooltip("One per BinnyFace, in enum order.")]
        [SerializeField] private Sprite[] _faces;
        [SerializeField] private Sprite[] _thrustLeftFrames;
        [SerializeField] private Sprite[] _thrustRightFrames;

        [Header("Gears")]
        [Tooltip("Degrees of gear per world unit travelled — they read as driven by the movement.")]
        [SerializeField] private float _degreesPerUnit = 120f;
        [Tooltip("Idle turn in degrees per second, so he never looks switched off.")]
        [SerializeField] private float _idleSpin = 20f;
        [Tooltip("Rotation is snapped to this. An 11px gear turned freely just smears; 0 = free.")]
        [SerializeField] private float _rotationStep = 15f;

        [Header("Thrust")]
        [Tooltip("Flame flipbook rate. Four frames at 12 is what the concept asks for.")]
        [SerializeField] private float _thrustFps = 12f;

        [Header("Lean")]
        [Tooltip("Most he tips into the direction of travel.")]
        [SerializeField] private float _maxTilt = 8f;
        [Tooltip("Degrees of tip per unit of horizontal speed, before the cap.")]
        [SerializeField] private float _tiltPerSpeed = 2f;
        [Tooltip("How fast the tip catches up. Higher is twitchier.")]
        [SerializeField] private float _tiltResponse = 7f;

        private Vector2 _velocity;
        private bool _thrusting;
        private BinnyFace _wanted = BinnyFace.Angry;
        private BinnyFace _shown = (BinnyFace)(-1);

        private float _gearAngle;
        private float _flameTime;
        private float _tilt;

        /// <summary>The face on the screen right now.</summary>
        public BinnyFace Face => _wanted;

        /// <summary>This frame's travel, in world units per second. Drives the gears and the lean.</summary>
        public void SetMotion(Vector2 velocity) => _velocity = velocity;

        /// <summary>Flames on while he is under way, off while he holds station.</summary>
        public void SetThrust(bool on) => _thrusting = on;

        /// <summary>Swap the screen. Free to call every frame — an unchanged face touches nothing.</summary>
        public void SetFace(BinnyFace face) => _wanted = face;

        private void LateUpdate()
        {
            float dt = Time.deltaTime;

            TurnGears(dt);
            BurnThrust(dt);
            Lean(dt);
            ShowFace();
        }

        /// <summary>
        /// Both gears turn the same way, against the direction of travel, so the left one looks
        /// like it is driving him along. Vertical movement still turns them — he is one machine,
        /// not a cart — but the sign comes off the horizontal, which is the readable part.
        /// </summary>
        private void TurnGears(float dt)
        {
            if (!_gearLeft && !_gearRight) return;

            float speed = _velocity.magnitude;
            float direction = Mathf.Abs(_velocity.x) > 0.01f ? -Mathf.Sign(_velocity.x) : 1f;

            _gearAngle += (speed * _degreesPerUnit * direction + _idleSpin) * dt;
            _gearAngle = Mathf.Repeat(_gearAngle, 360f);

            float shown = _rotationStep > 0f ? Mathf.Floor(_gearAngle / _rotationStep) * _rotationStep : _gearAngle;
            var rotation = Quaternion.Euler(0f, 0f, shown);

            if (_gearLeft) _gearLeft.transform.localRotation = rotation;
            if (_gearRight) _gearRight.transform.localRotation = rotation;
        }

        private void BurnThrust(float dt)
        {
            if (_thrustLeft) _thrustLeft.enabled = _thrusting;
            if (_thrustRight) _thrustRight.enabled = _thrusting;

            if (!_thrusting)
            {
                // Next burn starts on frame one rather than wherever the last one stopped.
                _flameTime = 0f;
                return;
            }

            _flameTime += dt * Mathf.Max(1f, _thrustFps);

            Frame(_thrustLeft, _thrustLeftFrames);
            Frame(_thrustRight, _thrustRightFrames);
        }

        private void Frame(SpriteRenderer renderer, Sprite[] frames)
        {
            if (!renderer || frames == null || frames.Length == 0) return;

            int index = Mathf.FloorToInt(_flameTime) % frames.Length;
            renderer.sprite = frames[index];
        }

        private void Lean(float dt)
        {
            float wanted = Mathf.Clamp(-_velocity.x * _tiltPerSpeed, -_maxTilt, _maxTilt);

            _tilt = Mathf.Lerp(_tilt, wanted, 1f - Mathf.Exp(-_tiltResponse * dt));
            transform.localRotation = Quaternion.Euler(0f, 0f, _tilt);
        }

        private void ShowFace()
        {
            if (_shown == _wanted || !_face) return;

            int index = (int)_wanted;
            if (_faces == null || index < 0 || index >= _faces.Length || !_faces[index]) return;

            _face.sprite = _faces[index];
            _shown = _wanted;
        }
    }
}
