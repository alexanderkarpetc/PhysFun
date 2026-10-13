using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// Keeps only the rooms near the player running. A floor is a dozen rooms in one scene,
    /// and before this every rope, enemy, saw and loose crate in all of them was simulated
    /// every step - the cost grew with every room added, whether anyone was in it or not.
    ///
    /// A room further than <see cref="SleepDistance"/> from the player is put to sleep: every
    /// non-static Rigidbody2D in it stops being simulated (out of the solver, the contact pass
    /// and the transform write-back), and every script in it that updates - enemies, ropes,
    /// damageables, machines - and every Animator is switched off. Within
    /// <see cref="WakeDistance"/> it wakes and carries on exactly where it stopped. The gap
    /// between the two keeps a room on the edge from flickering.
    ///
    /// Static bodies are left alone: they cost nothing while nothing touches them, and a
    /// deck that stopped colliding would drop whatever is lying on it that does not belong
    /// to the room (a corpse thrown in from next door). The terrain is one body for the whole
    /// floor and never sleeps. Things that left their room's hierarchy (ragdolls, debris)
    /// stay awake wherever they are.
    ///
    /// Distances are from the player to the room's template rectangle, in world units; the
    /// camera sees about 21 x 12, so a room wakes before it comes on screen.
    /// </summary>
    public sealed class RoomSleeper : MonoBehaviour
    {
        public static bool Enabled = true;
        public static float WakeDistance = 12f;
        public static float SleepDistance = 16f;
        public static float Interval = 0.25f;

        private static RoomSleeper _instance;
        private static readonly List<Room> Rooms = new();
        private static readonly Dictionary<Room, Asleep> Sleeping = new();
        private static readonly Dictionary<Type, bool> Updates = new();

        private float _next;

        /// <summary>What a sleeping room had running, to switch back on exactly that.</summary>
        private sealed class Asleep
        {
            public readonly List<Rigidbody2D> Bodies = new();
            public readonly List<Behaviour> Behaviours = new();
        }

        public static int SleepingCount => Sleeping.Count;
        public static bool IsAsleep(Room room) => Sleeping.ContainsKey(room);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlayMode()
        {
            Rooms.Clear();
            Sleeping.Clear();
            _instance = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Install()
        {
            if (_instance) return;
            var go = new GameObject("~RoomSleeper") { hideFlags = HideFlags.HideAndDontSave };
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<RoomSleeper>();
        }

        /// <summary>Called by a <see cref="Room"/> that is part of a floor.</summary>
        internal static void Register(Room room)
        {
            if (!Rooms.Contains(room)) Rooms.Add(room);
        }

        internal static void Unregister(Room room)
        {
            Rooms.Remove(room);
            Sleeping.Remove(room);
        }

        private void Update()
        {
            if (Time.time < _next) return;
            _next = Time.time + Interval;

            var player = App.Instance.PlayerGo;
            if (!Enabled || !player)
            {
                WakeAll();
                return;
            }
            Vector2 p = player.transform.position;
            for (int i = Rooms.Count - 1; i >= 0; i--)
            {
                var room = Rooms[i];
                if (!room)
                {
                    Rooms.RemoveAt(i);
                    continue;
                }
                float d = Distance(room, p);
                bool asleep = Sleeping.ContainsKey(room);
                if (asleep && d <= WakeDistance) Wake(room);
                else if (!asleep && d >= SleepDistance) Sleep(room);
            }
        }

        private static float Distance(Room room, Vector2 p)
        {
            var r = room.LocalRect;
            Vector2 min = (Vector2)room.transform.position + r.min;
            Vector2 max = min + r.size;
            float dx = Mathf.Max(min.x - p.x, 0f, p.x - max.x);
            float dy = Mathf.Max(min.y - p.y, 0f, p.y - max.y);
            return Mathf.Sqrt(dx * dx + dy * dy);
        }

        private static void Sleep(Room room)
        {
            var a = new Asleep();
            foreach (var rb in room.GetComponentsInChildren<Rigidbody2D>(true))
            {
                if (rb.bodyType == RigidbodyType2D.Static || !rb.simulated) continue;
                rb.simulated = false;
                a.Bodies.Add(rb);
            }
            foreach (var b in room.GetComponentsInChildren<Behaviour>(true))
            {
                if (!b.enabled || b is Room || !Runs(b)) continue;
                b.enabled = false;
                a.Behaviours.Add(b);
            }
            Sleeping[room] = a;
        }

        private static void Wake(Room room)
        {
            if (!Sleeping.TryGetValue(room, out var a)) return;
            Sleeping.Remove(room);
            foreach (var rb in a.Bodies)
                if (rb) rb.simulated = true;
            foreach (var b in a.Behaviours)
                if (b) b.enabled = true;
        }

        private static void WakeAll()
        {
            if (Sleeping.Count == 0) return;
            foreach (var room in new List<Room>(Sleeping.Keys)) Wake(room);
        }

        /// <summary>Does switching this off save anything: an Animator, or a script with an
        /// Update, FixedUpdate or LateUpdate of its own.</summary>
        private static bool Runs(Behaviour b)
        {
            if (b is Animator) return true;
            if (b is not MonoBehaviour) return false;
            var t = b.GetType();
            if (Updates.TryGetValue(t, out var runs)) return runs;
            const BindingFlags F = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            runs = t.GetMethod("FixedUpdate", F) != null || t.GetMethod("Update", F) != null ||
                   t.GetMethod("LateUpdate", F) != null;
            Updates[t] = runs;
            return runs;
        }
    }
}
