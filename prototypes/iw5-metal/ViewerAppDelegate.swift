import UIKit
import MetalKit

@main
final class ViewerAppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let w = UIWindow(frame: UIScreen.main.bounds)
        let vc = UIViewController()
        vc.view = IW5MeshPreviewView(frame: w.bounds, device: MTLCreateSystemDefaultDevice())
        w.rootViewController = vc
        w.makeKeyAndVisible()
        window = w
        return true
    }
}
