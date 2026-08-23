using UnityEngine;

namespace Siege
{
    /// <summary>
    /// Noita-style camera. It rides the player, leans toward wherever the cursor points so you
    /// can see what you are about to do to the world, and frames the view as a fixed number of
    /// art pixels so everything reads at the scale the sprites were drawn for.
    ///
    /// <see cref="CameraShake"/> owns the transform whenever one is attached, so this only ever
    /// hands it a resting position - a kick is never quietly overwritten. Runs early so the
    /// shake sees this frame's rest, not the last one.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    [DefaultExecutionOrder(-100)]
    public sealed class CameraFollow : MonoBehaviour
    {
        [Header("Target")]
        [Tooltip("Leave empty to follow the player.")]
        [SerializeField] private Transform _target;
        [Tooltip("Where to sit relative to the target. The player pivot is already about chest " +
                 "height, so this only needs a nudge.")]
        [SerializeField] private Vector2 _targetOffset = new(0f, 0.15f);

        [Header("Framing")]
        [Tooltip("Art scale. Sprites in this project import at 20 pixels per unit.")]
        [SerializeField] private float _pixelsPerUnit = 20f;
        [Tooltip("View height in art pixels. Noita renders 427x242, so 242 frames the world the " +
                 "same way it does. 240 is the value that scales by an exact 3x at 720p. " +
                 "Set to 0 to leave the orthographic size to something else, e.g. a " +
                 "Pixel Perfect Camera.")]
        [SerializeField] private float _viewHeightPixels = 242f;
        [Tooltip("Keep the camera on whole art pixels. Stops pixel art shimmering as it moves.")]
        [SerializeField] private bool _snapToPixelGrid = true;

        [Header("Follow")]
        [Tooltip("Roughly how long the camera takes to catch up. 0 pins it to the target.")]
        [SerializeField] private float _followLag = 0.12f;
        [Tooltip("Seconds of the target's own velocity to lead by, so fast flight is not blind.")]
        [SerializeField] private float _velocityLead = 0.1f;
        [SerializeField] private float _maxVelocityLead = 1.5f;

        [Header("Cursor lean")]
        [Tooltip("How far toward the cursor the view slides, as a fraction of the way there.")]
        [Range(0f, 0.9f)]
        [SerializeField] private float _cursorWeight = 0.32f;
        [Tooltip("Hard cap on the lean, in units. Keeps the player away from the screen edge.")]
        [SerializeField] private Vector2 _maxCursorLean = new(3.2f, 1.8f);
        [SerializeField] private float _cursorLag = 0.14f;

        private Camera _cam;
        private CameraShake _shake;
        private Transform _follow;
        private Rigidbody2D _body;
        private Vector2 _pos, _posVel, _lean, _leanVel;

        /// <summary>Half-height of the view in units, i.e. the orthographic size it wants.</summary>
        public float FramedSize =>
            _pixelsPerUnit > 0f ? _viewHeightPixels / (2f * _pixelsPerUnit) : 0f;

        private void Awake()
        {
            _cam = GetComponent<Camera>();
            _shake = GetComponent<CameraShake>();
            _pos = transform.position;
        }

        private void Start() => Snap();

        /// <summary>Jump straight to the framed position with no glide. Use it after a teleport.</summary>
        public void Snap()
        {
            ApplyFraming();

            var t = Resolve();
            if (!t) return;

            _lean = _leanVel = _posVel = Vector2.zero;
            _pos = Anchor(t);
            Commit(_pos);
        }

        private void LateUpdate()
        {
            ApplyFraming();

            var t = Resolve();
            if (!t) return;

            Vector2 want = Anchor(t) + Lean();
            _pos = _followLag > 0f
                ? Vector2.SmoothDamp(_pos, want, ref _posVel, _followLag)
                : want;

            Commit(_pos);
        }

        private Transform Resolve()
        {
            // The player registers itself in Awake, so this lands on the very first frame.
            Transform t = _target ? _target : App.Instance.PlayerTransform;
            if (t != _follow)
            {
                _follow = t;
                _body = t ? t.GetComponent<Rigidbody2D>() : null;
            }
            return t;
        }

        private Vector2 Anchor(Transform t)
        {
            Vector2 a = (Vector2)t.position + _targetOffset;

            if (_body && _velocityLead > 0f)
                a += Vector2.ClampMagnitude(_body.linearVelocity * _velocityLead, _maxVelocityLead);

            return a;
        }

        private Vector2 Lean()
        {
            Vector2 want = Vector2.zero;

            if (_cursorWeight > 0f && Screen.height > 0)
            {
                // Measured from the centre of the screen, not from the cursor's world position:
                // that position moves with the camera, so leaning on it would chase its own tail.
                Vector3 m = Input.mousePosition;
                var off = new Vector2(m.x - Screen.width * 0.5f, m.y - Screen.height * 0.5f);
                float unitsPerPixel = _cam.orthographicSize * 2f / Screen.height;

                want = off * (unitsPerPixel * _cursorWeight);
                want.x = Mathf.Clamp(want.x, -_maxCursorLean.x, _maxCursorLean.x);
                want.y = Mathf.Clamp(want.y, -_maxCursorLean.y, _maxCursorLean.y);
            }

            _lean = _cursorLag > 0f
                ? Vector2.SmoothDamp(_lean, want, ref _leanVel, _cursorLag)
                : want;

            return _lean;
        }

        private void Commit(Vector2 p)
        {
            if (_snapToPixelGrid && _pixelsPerUnit > 0f)
            {
                p.x = Mathf.Round(p.x * _pixelsPerUnit) / _pixelsPerUnit;
                p.y = Mathf.Round(p.y * _pixelsPerUnit) / _pixelsPerUnit;
            }

            var rest = new Vector3(p.x, p.y, transform.position.z);

            if (_shake) _shake.SetRest(rest);
            else transform.position = rest;
        }

        private void ApplyFraming()
        {
            if (!_cam || !_cam.orthographic) return;

            float size = FramedSize;
            if (size > 0f && !Mathf.Approximately(_cam.orthographicSize, size))
                _cam.orthographicSize = size;
        }

#if UNITY_EDITOR
        // Reframe live while tuning, so the scene view shows what the game will show.
        private void OnValidate()
        {
            if (!_cam) _cam = GetComponent<Camera>();
            ApplyFraming();
        }
#endif
    }
}
