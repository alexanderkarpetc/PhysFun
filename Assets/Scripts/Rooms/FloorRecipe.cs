using System.Collections.Generic;
using Materials;
using UnityEngine;

namespace Rooms
{
    /// <summary>
    /// What a floor is made of: which rooms it may draw from, how many it uses, and how the
    /// space between them is filled and cut. <see cref="FloorBuilder"/> turns one of these and
    /// a seed into a single terrain.
    /// </summary>
    [CreateAssetMenu(menuName = "PhysFun/Floor Recipe", fileName = "Floor")]
    public sealed class FloorRecipe : ScriptableObject
    {
        [Tooltip("Room prefabs to pick from. Each is used at most once per floor.")]
        [SerializeField] private List<Room> _rooms = new();
        [Tooltip("Rooms per floor; capped by how many rooms there are.")]
        [SerializeField, Min(1)] private int _roomCount = 4;
        [Tooltip("The room the floor starts in. Empty = any.")]
        [SerializeField] private Room _startRoom;

        [Header("Fill")]
        [Tooltip("Tile for everything that is not a room or a corridor. Same physics as the " +
                 "rooms' rock - only the look differs, so the eye can tell the two apart.")]
        [SerializeField] private string _fillTile = "rock_hard";
        [SerializeField] private PhysMaterialId _fillMaterial = PhysMaterialId.Default;
        [Tooltip("Back wall everywhere a room does not give its own - behind the corridors and " +
                 "whatever gets dug into the fill. Drawn darkened by TerrainBackdrop. Empty = none.")]
        [SerializeField] private string _backTile = "rock_hard";
        [Tooltip("Solid fill kept round the outside of the floor, in world units.")]
        [SerializeField, Min(1f)] private float _margin = 6f;

        [Header("Layout")]
        [Tooltip("Least fill between two rooms side by side, in world units. Rooms sit on a " +
                 "grid of cells this much bigger than the biggest room.")]
        [SerializeField, Min(1f)] private float _gap = 5f;
        [Tooltip("How far a room may wander inside its grid cell, as a fraction of the slack.")]
        [SerializeField, Range(0f, 1f)] private float _jitter = 0.35f;
        [Tooltip("Corridors added on top of the tree that joins every room, so there is more " +
                 "than one way round.")]
        [SerializeField, Min(0)] private int _extraLinks = 1;

        [Header("Corridors")]
        [Tooltip("Corridor bore, in world units - its height where it runs level, its width " +
                 "where it climbs. The player is a little over 1 unit tall.")]
        [SerializeField, Min(0.5f)] private float _corridorSize = 1.6f;

        public IReadOnlyList<Room> Rooms => _rooms;
        public int RoomCount => _roomCount;
        public Room StartRoom => _startRoom;
        public string FillTile => _fillTile;
        public PhysMaterialId FillMaterial => _fillMaterial;
        public string BackTile => _backTile;
        public float Margin => _margin;
        public float Gap => _gap;
        public float Jitter => _jitter;
        public int ExtraLinks => _extraLinks;
        public float CorridorSize => _corridorSize;
    }
}
