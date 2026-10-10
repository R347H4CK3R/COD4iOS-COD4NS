// Native iOS Metal glTF viewer foundation (standalone prototype).
// Integrate into an iOS Xcode target after testing on macOS/Xcode.
// This deliberately draws a known geometry triangle first, to verify
// render loop/device/pipeline before importing the user's private models.
import UIKit
import MetalKit

final class IW5MetalSmokeView: MTKView, MTKViewDelegate {
    private var commandQueue: MTLCommandQueue?
    private var pipeline: MTLRenderPipelineState?
    private var triangle: MTLBuffer?

    required init(coder: NSCoder) {
        super.init(coder: coder)
        configure()
    }
    override init(frame: CGRect, device: MTLDevice?) {
        super.init(frame: frame, device: device)
        configure()
    }
    private func configure() {
        self.device = self.device ?? MTLCreateSystemDefaultDevice()
        guard let device = self.device else { return }
        colorPixelFormat = .bgra8Unorm
        clearColor = MTLClearColor(red: 0.03, green: 0.04, blue: 0.06, alpha: 1)
        preferredFramesPerSecond = 60
        framebufferOnly = true
        commandQueue = device.makeCommandQueue()
        let shader = """
        #include <metal_stdlib>
        using namespace metal;
        struct V { float2 pos; float3 color; };
        struct Out { float4 position [[position]]; float3 color; };
        vertex Out vert_main(const device V *v [[buffer(0)]], uint id [[vertex_id]]) {
            Out o; o.position=float4(v[id].pos,0,1); o.color=v[id].color; return o;
        }
        fragment float4 frag_main(Out in [[stage_in]]) { return float4(in.color,1); }
        """
        do {
            let library = try device.makeLibrary(source: shader, options: nil)
            let descriptor = MTLRenderPipelineDescriptor()
            descriptor.vertexFunction = library.makeFunction(name: "vert_main")
            descriptor.fragmentFunction = library.makeFunction(name: "frag_main")
            descriptor.colorAttachments[0].pixelFormat = colorPixelFormat
            pipeline = try device.makeRenderPipelineState(descriptor: descriptor)
        } catch {
            print("IW5 Metal smoke pipeline failed: \(error)")
            return
        }
        let vertices: [Float] = [
            0,0.7, 1,0.2,0.2,
            -0.7,-0.7, 0.2,1,0.2,
            0.7,-0.7, 0.2,0.4,1
        ]
        triangle = vertices.withUnsafeBytes { data in
            device.makeBuffer(bytes: data.baseAddress!, length: data.count, options: [])
        }
        delegate = self
    }
    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}
    func draw(in view: MTKView) {
        guard let drawable = currentDrawable,
              let pass = currentRenderPassDescriptor,
              let queue = commandQueue,
              let pipeline = pipeline,
              let vertexBuffer = triangle,
              let command = queue.makeCommandBuffer(),
              let encoder = command.makeRenderCommandEncoder(descriptor: pass)
        else { return }
        encoder.setRenderPipelineState(pipeline)
        encoder.setVertexBuffer(vertexBuffer, offset: 0, index: 0)
        encoder.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        encoder.endEncoding()
        command.present(drawable)
        command.commit()
    }
}
