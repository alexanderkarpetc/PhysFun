using UnityEngine;

public class App
{
    public static App Instance { get; } = new App();
    public Transform PlayerTransform { get; set; }
    public GameObject PlayerGo { get; set; }
}
