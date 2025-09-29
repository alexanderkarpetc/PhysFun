using UnityEngine;

public class App
{
    public static App Instance { get; } = new();

    public Transform PlayerTransform { get; set; }
    public GameObject PlayerGo { get; set; }
    public Hud Hud { get; } = new();
}
