namespace Binny
{
    /// <summary>
    /// What the screen shows. The names are the file names in <c>GameConcepts/Binny/Faces</c>
    /// (<c>Binny_Face_Angry.png</c> and so on) — the builder fills the view's sprite list by
    /// walking this enum, so a new face is a new drawing plus a new entry here, nothing else.
    /// The order is what the list is indexed by, so add to the end rather than in the middle.
    /// </summary>
    public enum BinnyFace
    {
        Neutral,
        Angry,
        Happy,
        Sad,
        Mad,
        Surprised,
        Sleep,
        Dead,
        Glitch,
        Talk01,
        Talk02,
    }
}
