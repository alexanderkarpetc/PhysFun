using Common;
using UnityEngine;

namespace Weapons
{
    /// <summary>
    /// Puts a <see cref="WeaponDefinition"/>'s sprite in a creature's hand, points it where the
    /// creature is shooting, and fires it.
    ///
    /// Swapping the asset in the inspector redraws it immediately, in edit mode as well as play,
    /// so a soldier standing in the scene can be handed any gun without entering play mode.
    ///
    /// The renderer it drives is expected to live under whatever the creature flips — on the
    /// soldier that is View, whose localScale.x the controller negates. Aiming is done in that
    /// mirrored space on purpose: the gun keeps reading correctly when it faces left, and this
    /// component never has to ask which way the body is turned.
    ///
    /// Rounds fall. <see cref="Aim"/> works out the elevation that lands one on a point rather
    /// than pointing flat at it, so a slow gun visibly tilts up at range and a fast one barely
    /// moves — the arc is what tells the two apart.
    /// </summary>
    [ExecuteAlways]
    [AddComponentMenu("PhysFun/Weapon Holder")]
    public sealed class WeaponHolder : MonoBehaviour
    {
        [Tooltip("The gun this creature carries. Swap it to hand them a different one.")]
        [SerializeField] private WeaponDefinition weapon;

        [Tooltip("Renderer that draws the gun, pivoted on the grip. It hangs under the Weapon " +
                 "node, whose position the clips key so the gun rides the walk bob; this one is " +
                 "left alone by the animator and carries the per-weapon hold offset instead.")]
        [SerializeField] private SpriteRenderer view;

        [Tooltip("The node that swings when aiming — the renderer's parent, whose position the " +
                 "clips key. Falls back to that parent when left empty.")]
        [SerializeField] private Transform arm;

        [Tooltip("Spawned per round. Its sprite, damage and gravity come from the weapon, so " +
                 "one prefab serves every gun.")]
        [SerializeField] private Projectile projectilePrefab;

        [Tooltip("Body to shove back on recoil. Found on a parent when left empty.")]
        [SerializeField] private Rigidbody2D shooter;

        [Tooltip("Beam drawn from the muzzle while a gun with Laser Sight winds up. A one-pixel " +
                 "sprite pivoted on its left edge, stretched to reach — it hangs off the root " +
                 "rather than the flipped visuals so the mirror cannot skew it.")]
        [SerializeField] private SpriteRenderer laser;

        /// <summary>Elevation the last <see cref="Aim"/> settled on, in degrees.</summary>
        private float _aimDegrees;

        private float _nextShot;
        private int _left = -1;
        private float _reloadDone;

        private int _burstLeft;
        private float _windUpEnds;
        private Vector2 _aimPoint;
        private bool _aiming;

        /// <summary>The gun in hand. Assigning redraws it and refills it.</summary>
        public WeaponDefinition Weapon
        {
            get => weapon;
            set
            {
                weapon = value;
                _left = -1;
                Apply();
            }
        }

        /// <summary>Where a shot leaves from, in world space. Follows the flip and the aim.</summary>
        public Vector2 MuzzlePosition =>
            view && weapon
                ? (Vector2)view.transform.TransformPoint(weapon.muzzleOffset)
                : (Vector2)transform.position;

        /// <summary>Where the gun points, in world space. Follows the flip and the aim.</summary>
        ///
        /// TransformVector, not TransformDirection: the body is flipped by negating
        /// localScale.x, and TransformDirection ignores scale outright. Using it here pointed
        /// the shot one way while the mirrored sprite drew the barrel the other.
        public Vector2 AimDirection =>
            view ? ((Vector2)view.transform.TransformVector(Vector3.right)).normalized
                 : Vector2.right;

        /// <summary>Rounds left before a reload. -1 when there is no weapon.</summary>
        public int RoundsLeft => _left;

        public bool Reloading => _left == 0 && _reloadDone > 0f && Time.time < _reloadDone;

        private void OnEnable() => Apply();

        private void OnValidate() => Apply();

        // ------------------------------------------------------------------- look

        /// <summary>Push the definition onto the renderer. Safe to call whenever.</summary>
        public void Apply()
        {
            if (!view) return;

            // The definition owns all three; the renderer is only where they land. Writing
            // them unconditionally would mark the scene dirty on every load, so each one is
            // only pushed when it actually differs.
            Sprite sprite = weapon ? weapon.sprite : null;
            if (view.sprite != sprite) view.sprite = sprite;

            if (!weapon) return;

            if (view.sortingOrder != weapon.sortingOrder) view.sortingOrder = weapon.sortingOrder;

            // Safe because the animator keys the parent, not this node.
            Vector3 hold = weapon.holdOffset;
            if (view.transform.localPosition != hold) view.transform.localPosition = hold;
        }

        // -------------------------------------------------------------------- aim

        /// <summary>
        /// Swing the gun onto <paramref name="worldTarget"/>, allowing for the drop on the way.
        /// Returns false when the shot cannot reach, and leaves the gun at the flattest elevation
        /// that gets closest.
        /// </summary>
        public bool Aim(Vector2 worldTarget)
        {
            if (!weapon || !view) return false;

            Transform node = Arm;
            Vector2 from = MuzzlePosition;
            Vector2 delta = worldTarget - from;

            bool reaches = Ballistics.LaunchAngle(
                delta, weapon.fire.projectileSpeed, Gravity, out float worldDegrees);

            // Back out the local angle that comes out pointing this way once the parent's
            // mirror has been applied. InverseTransformVector carries the scale; its
            // Direction sibling drops it, which is the whole flip.
            Vector2 world = new(Mathf.Cos(worldDegrees * Mathf.Deg2Rad),
                                Mathf.Sin(worldDegrees * Mathf.Deg2Rad));
            Vector2 local = node.parent ? (Vector2)node.parent.InverseTransformVector(world) : world;

            _aimDegrees = Mathf.Atan2(local.y, local.x) * Mathf.Rad2Deg;
            node.localRotation = Quaternion.Euler(0f, 0f, _aimDegrees);
            _aimPoint = worldTarget;
            _aiming = true;
            return reaches;
        }

        /// <summary>Drop the gun back to level, for when the creature stops shooting.</summary>
        public void ClearAim()
        {
            // Letting go also drops a half-finished burst and any spin-up, so a minigun that
            // loses its target has to wind up again rather than picking up mid-swarm.
            _aiming = false;
            _burstLeft = 0;
            _windUpEnds = 0f;
            ShowLaser(false);

            if (!view) return;
            _aimDegrees = 0f;
            Arm.localRotation = Quaternion.identity;
        }

        private Transform Arm =>
            arm ? arm : (view.transform.parent ? view.transform.parent : view.transform);

        /// <summary>Downward pull on this gun's rounds, in units per second squared.</summary>
        private float Gravity =>
            weapon ? Physics2D.gravity.magnitude * weapon.fire.gravity : 0f;

        // ------------------------------------------------------------------- fire

        /// <summary>
        /// Fire if the gun is ready. Call it every frame while the trigger is down: the rate,
        /// the burst and the reload are all handled here.
        /// </summary>
        public bool TryFire()
        {
            if (!weapon || !projectilePrefab || !Application.isPlaying) return false;

            FireProfile f = weapon.fire;
            if (_left < 0) _left = Mathf.Max(1, f.magazine);

            if (Time.time < _nextShot) return false;

            // Between bursts: reload if the magazine ran dry, then spin up.
            if (_burstLeft <= 0)
            {
                if (_left == 0)
                {
                    if (_reloadDone <= 0f) _reloadDone = Time.time + Mathf.Max(0.1f, f.reloadTime);
                    if (Time.time < _reloadDone) return false;
                    _left = Mathf.Max(1, f.magazine);
                    _reloadDone = 0f;
                }

                if (f.windUp > 0f)
                {
                    if (_windUpEnds <= 0f) _windUpEnds = Time.time + f.windUp;
                    if (f.laserSight) ShowLaser(true);
                    if (Time.time < _windUpEnds) return false;
                }

                _windUpEnds = 0f;
                ShowLaser(false);
                _burstLeft = Mathf.Max(1, f.burst);
            }

            FireOne(f);
            _left = Mathf.Max(0, _left - 1);
            _burstLeft--;

            // Out of rounds mid-burst ends the burst early; the reload happens next time round.
            if (_left == 0) _burstLeft = 0;

            _nextShot = Time.time + (_burstLeft > 0
                ? 1f / Mathf.Max(0.01f, f.rate)
                : Mathf.Max(0.02f, f.burstCooldown));
            return true;
        }

        /// <summary>Stretch the beam from the muzzle to whatever is being aimed at.</summary>
        private void ShowLaser(bool on)
        {
            if (!laser) return;

            if (!on || !_aiming)
            {
                if (laser.enabled) laser.enabled = false;
                return;
            }

            Vector2 from = MuzzlePosition;
            Vector2 to = _aimPoint;
            Vector2 span = to - from;
            float len = span.magnitude;
            if (len < 0.01f) { laser.enabled = false; return; }

            Transform t = laser.transform;
            t.position = from;
            t.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(span.y, span.x) * Mathf.Rad2Deg);

            // The sprite is one pixel wide, pivoted on its left edge, so the scale that makes
            // it reach is the distance over the size of that pixel.
            float pixel = laser.sprite ? 1f / laser.sprite.pixelsPerUnit : 0.05f;
            t.localScale = new Vector3(len / pixel, 1f, 1f);

            if (!laser.enabled) laser.enabled = true;
        }

        private void FireOne(FireProfile f)
        {
            Vector2 from = MuzzlePosition;
            Vector2 aim = AimDirection;

            for (int p = 0; p < Mathf.Max(1, f.pellets); p++)
            {
                float jitter = f.spread > 0f ? Random.Range(-f.spread, f.spread) : 0f;
                Vector2 dir = (Vector2)(Quaternion.Euler(0f, 0f, jitter) * aim);

                var round = Instantiate(projectilePrefab, from, Quaternion.identity);
                round.Fire(dir * f.projectileSpeed, gameObject, f.damage,
                           f.gravity, weapon.projectile);
            }

            if (f.recoil <= 0f) return;
            if (!shooter) shooter = GetComponentInParent<Rigidbody2D>();
            if (shooter) shooter.AddForce(-aim * f.recoil, ForceMode2D.Impulse);
        }

        private void LateUpdate()
        {
            if (laser && laser.enabled) ShowLaser(true);
        }

        private void OnDrawGizmosSelected()
        {
            if (!view || !weapon) return;

            Vector2 muzzle = MuzzlePosition;
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(muzzle, 0.03f);

            // The arc the current aim would actually throw a round along.
            Vector2 v = AimDirection * weapon.fire.projectileSpeed;
            Vector2 prev = muzzle;
            for (int i = 1; i <= 24; i++)
            {
                float t = i * 0.04f;
                Vector2 at = muzzle + v * t + 0.5f * Gravity * t * t * Vector2.down;
                Gizmos.DrawLine(prev, at);
                prev = at;
            }
        }
    }

    /// <summary>Where a thrown round ends up.</summary>
    public static class Ballistics
    {
        /// <summary>
        /// Elevation, in world degrees, that puts a round launched at <paramref name="speed"/>
        /// onto a point <paramref name="delta"/> away under <paramref name="gravity"/>.
        ///
        /// Of the two arcs that hit, this takes the flat one — the fast, direct shot rather than
        /// the lob. Out of range, it returns the 45° that carries furthest, aimed at the target,
        /// and reports false so the caller can decide not to waste the round.
        /// </summary>
        public static bool LaunchAngle(Vector2 delta, float speed, float gravity, out float degrees)
        {
            if (gravity <= 0.0001f || speed <= 0.0001f)
            {
                degrees = Mathf.Atan2(delta.y, delta.x) * Mathf.Rad2Deg;
                return true;
            }

            float side = delta.x >= 0f ? 1f : -1f;
            float x = Mathf.Abs(delta.x);
            float y = delta.y;

            if (x < 0.0001f)
            {
                degrees = y >= 0f ? 90f : -90f;
                return true;
            }

            float v2 = speed * speed;
            float disc = v2 * v2 - gravity * (gravity * x * x + 2f * y * v2);
            if (disc < 0f)
            {
                degrees = side >= 0f ? 45f : 135f;
                return false;
            }

            float elevation = Mathf.Atan((v2 - Mathf.Sqrt(disc)) / (gravity * x)) * Mathf.Rad2Deg;
            degrees = side >= 0f ? elevation : 180f - elevation;
            return true;
        }
    }
}
