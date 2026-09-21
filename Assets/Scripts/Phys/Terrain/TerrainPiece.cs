using System.Collections.Generic;
using Materials;
using Spawners;
using UnityEngine;

namespace Phys.Terrain
{
    /// <summary>
    /// A lump of terrain that has broken loose in one go.
    ///
    /// Terrain is chunked for editing, not for physics: the chunk grid exists so that carving a
    /// hole only re-uploads and re-traces one texture. That is invisible right up until a piece
    /// falls, and then it is the most visible thing on screen — six chunks that were one wall a
    /// frame ago become six rigid bodies, overlap each other by the pixel their colliders share,
    /// and shove themselves apart. A slab comes down looking like a dropped stack of bricks.
    ///
    /// So chunks that come loose together are welded: they are reparented under one object that
    /// carries the only <see cref="Rigidbody2D"/>, and their colliders — having no body of their
    /// own any more — all belong to it. One body, one centre of mass, one impact. Nothing else
    /// changes: each chunk keeps its own sprite, texture and traced collider, so the eraser,
    /// fire, the split scan and the fracture model go on working on it exactly as before.
    ///
    /// Welding has to work in both directions, and that is what <see cref="Repartition"/> is
    /// for. A fallen slab is still something you can shoot, burn and crack, and when one of
    /// those divides it, the halves are still children of one body: the seam appears and
    /// nothing moves. So whenever the set of children changes — a split hands back two where
    /// there was one, fire eats the last pixel of another — the piece works out which of its
    /// children are still one lump and hands the rest their own bodies. The test is
    /// <see cref="TerrainSupportSystem.Touching"/>, the same one that decided the piece should
    /// fall in the first place, so a crack means the same thing before and after the landing.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class TerrainPiece : MonoBehaviour
    {
        private int _lastChildCount = -1;

        // Repartition scratch. Pieces are rare and never repartition in parallel.
        private static readonly List<GameObject> Members = new();
        private static readonly List<Collider2D> MemberCols = new();
        private static readonly List<int> Comp = new();
        private static readonly List<GameObject> Chunk = new();
        private static bool[] _taken = new bool[16];

        /// <summary>
        /// Weld <paramref name="group"/> into a single falling body and return it. A group of
        /// one is not worth an extra object, so it just breaks loose on its own.
        ///
        /// The members must already be known to belong together — <see cref="TerrainSupportSystem"/>
        /// works that out from the same touching test it uses for support, so what ends up in
        /// one body is exactly what was one connected lump of terrain.
        /// </summary>
        public static GameObject Weld(List<TerrainBody> group)
        {
            if (group == null || group.Count == 0) return null;

            Members.Clear();
            foreach (var body in group)
            {
                if (!body || !body.Release()) continue;
                Members.Add(body.gameObject);
            }
            if (Members.Count == 0) return null;

            if (Members.Count == 1)
            {
                Solo(Members[0], Vector2.zero, 0f);
                return Members[0];
            }

            return Assemble(Members, Members[0].transform.parent, Vector2.zero, 0f);
        }

        /// <summary>
        /// Build one body out of <paramref name="members"/>: an object in the middle of them
        /// carrying the rigidbody, with every member reparented under it and stripped of its own.
        /// </summary>
        private static GameObject Assemble(List<GameObject> members, Transform parent,
                                           Vector2 velocity, float angularVelocity)
        {
            // Put the new object in the middle of what it is made of, so the body's transform is
            // somewhere inside the piece rather than off at a chunk corner.
            var bounds = new Bounds();
            bool haveBounds = false;
            foreach (var member in members)
            {
                var col = member.GetComponent<Collider2D>();
                if (!col) continue;
                if (!haveBounds) { bounds = col.bounds; haveBounds = true; }
                else bounds.Encapsulate(col.bounds);
            }

            var piece = new GameObject("terrain_piece") { layer = members[0].layer };
            piece.transform.SetParent(parent, false);
            piece.transform.position = haveBounds ? bounds.center : members[0].transform.position;
            piece.transform.rotation = Quaternion.identity;

            PhysMaterialId dominant = PhysMaterialId.Default;
            float dominantArea = -1f;
            float mass = 0f;

            foreach (var member in members)
            {
                // Any body of its own has to go, or the member's collider stays attached to it
                // and the weld achieves nothing. Destroy is deferred to the end of the frame,
                // which is harmless: until then the member is simply still its own body.
                var own = member.GetComponent<Rigidbody2D>();
                if (own) Destroy(own);

                member.transform.SetParent(piece.transform, true);

                float area = AreaOf(member);
                var material = MaterialLibrary.Of(member);
                mass += area * material.Density;

                // A piece of mixed material answers as whatever most of it is made of. It is
                // what the impact rules read for hardness, and what decides whether the piece
                // as a whole is brittle.
                if (area <= dominantArea) continue;
                dominantArea = area;
                dominant = material.Id;
            }

            // Tagging the piece rather than leaving it bare is what keeps the rest of the game
            // able to read it: the impact rules look the material up on the body they were hit
            // by, not on the sprite, and a brittle piece needs its contact hook up here too
            // because collision messages go to the object that owns the rigidbody.
            MaterialView.Apply(piece, dominant);

            var rb = piece.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Dynamic;
            rb.simulated = true;
            // The same figure MassRecalculator arrives at for a single body, summed over the
            // parts: it cannot be asked for it directly, because the members' colliders do not
            // belong to this body until their own ones are gone at the end of the frame.
            rb.mass = Mathf.Max(0.01f, mass * 100f);
            rb.linearVelocity = velocity;
            rb.angularVelocity = angularVelocity;

            piece.AddComponent<TerrainPiece>();
            return piece;
        }

        /// <summary>A single chunk falling on its own — no wrapper, just give it a body.</summary>
        private static void Solo(GameObject go, Vector2 velocity, float angularVelocity)
        {
            var rb = go.GetComponent<Rigidbody2D>();
            if (!rb) rb = go.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Dynamic;
            rb.simulated = true;
            MassRecalculator.SetMass(null, rb, go.GetComponent<Collider2D>());
            rb.linearVelocity = velocity;
            rb.angularVelocity = angularVelocity;
        }

        private static float AreaOf(GameObject go)
        {
            var col = go.GetComponent<Collider2D>();
            return col switch
            {
                PolygonCollider2D poly => MassRecalculator.GetArea(poly),
                CircleCollider2D circle => MassRecalculator.GetArea(circle),
                _ => 0f,
            };
        }

        /// <summary>
        /// Re-weigh the piece from what is left of it. Carving and burning go on after the weld,
        /// and a slab eaten down to a corner should not still land like a slab.
        /// </summary>
        public void RecalculateMass()
        {
            var rb = GetComponent<Rigidbody2D>();
            if (!rb) return;

            float mass = 0f;
            for (int i = 0; i < transform.childCount; i++)
            {
                var child = transform.GetChild(i).gameObject;
                mass += AreaOf(child) * MaterialLibrary.Of(child).Density;
            }
            rb.mass = Mathf.Max(0.01f, mass * 100f);
        }

        /// <summary>
        /// Work out whether this piece is still one lump, and hand out separate bodies if it is
        /// not. What divided it — a crack run through it where it lies, a hole burnt or erased
        /// through its waist — does not matter; all of them show up here as children that no
        /// longer reach each other.
        /// </summary>
        private void Repartition()
        {
            Members.Clear();
            MemberCols.Clear();
            for (int i = 0; i < transform.childCount; i++)
            {
                var child = transform.GetChild(i);
                var col = child.GetComponent<Collider2D>();
                if (!col) continue;
                Members.Add(child.gameObject);
                MemberCols.Add(col);
            }

            int n = Members.Count;
            if (n <= 1) { RecalculateMass(); return; }

            if (_taken.Length < n) _taken = new bool[Mathf.NextPowerOfTwo(n)];
            for (int i = 0; i < n; i++) _taken[i] = false;

            var rb = GetComponent<Rigidbody2D>();
            Vector2 velocity = rb ? rb.linearVelocity : Vector2.zero;
            float angular = rb ? rb.angularVelocity : 0f;
            var parent = transform.parent;

            // The first component found keeps this object — there is no reason to prefer any
            // particular one, and keeping one saves rebuilding a body that is already right.
            bool kept = false;

            for (int seed = 0; seed < n; seed++)
            {
                if (_taken[seed]) continue;

                Comp.Clear();
                Comp.Add(seed);
                _taken[seed] = true;

                for (int q = 0; q < Comp.Count; q++)
                {
                    var ca = MemberCols[Comp[q]];
                    for (int j = 0; j < n; j++)
                    {
                        if (_taken[j]) continue;
                        if (!TerrainSupportSystem.Touching(ca, MemberCols[j])) continue;
                        _taken[j] = true;
                        Comp.Add(j);
                    }
                }

                if (!kept) { kept = true; continue; }

                // Everything after the first is no longer attached to this body. It leaves with
                // the motion it had, so a slab that splits mid-fall keeps falling rather than
                // stopping dead and starting again.
                Chunk.Clear();
                for (int c = 0; c < Comp.Count; c++) Chunk.Add(Members[Comp[c]]);

                if (Chunk.Count == 1)
                {
                    Chunk[0].transform.SetParent(parent, true);
                    Solo(Chunk[0], velocity, angular);
                }
                else
                {
                    Assemble(Chunk, parent, velocity, angular);
                }
            }

            RecalculateMass();
        }

        private void Update()
        {
            // Children come and go on their own: the split scan replaces one with two, and the
            // registry deletes one whose last pixel has been erased or burnt away. Both show up
            // here as the count changing, which is cheap enough to watch every frame and saves
            // hanging listeners off the registry for something this small.
            int count = transform.childCount;
            if (count == _lastChildCount) return;
            _lastChildCount = count;

            if (count == 0) { Destroy(gameObject); return; }
            Repartition();

            // Repartition moves children out, so the count it should be compared against next
            // frame is the one left behind, not the one that triggered it.
            _lastChildCount = transform.childCount;
        }
    }
}
