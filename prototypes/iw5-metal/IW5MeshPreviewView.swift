// Isolated iOS Metal preview for IWM1 triangle streams.
// This is a geometry smoke test, not an IW5 runtime or full glTF renderer.
import Foundation
import MetalKit

final class IW5MeshPreviewView: MTKView, MTKViewDelegate {
    private var queue: MTLCommandQueue?
    private var pipeline: MTLRenderPipelineState?
    private var meshBuffer: MTLBuffer?
    private var vertexCount = 0

    required init(coder: NSCoder) {
        super.init(coder: coder)
        setup()
    }
    override init(frame: CGRect, device: MTLDevice?) {
        super.init(frame: frame, device: device)
        setup()
    }

    private func setup() {
        self.device = self.device ?? MTLCreateSystemDefaultDevice()
        guard let device = self.device else { return }
        colorPixelFormat = .bgra8Unorm
        preferredFramesPerSecond = 60
        clearColor = MTLClearColor(red: 0.04, green: 0.04, blue: 0.06, alpha: 1)
        queue = device.makeCommandQueue()
        let source = """
        #include <metal_stdlib>
        using namespace metal;
        struct Out { float4 pos [[position]]; float3 col; };
        vertex Out iw5_vert(const device packed_float3 *positions [[buffer(0)]],
                            constant float4 &bounds [[buffer(1)]], uint id [[vertex_id]]) {
            float3 p = float3(positions[id]);
            Out o;
            // Orthographic XY diagnostic view; bounds = center xyz and inverse scale.
            o.pos = float4((p.xy - bounds.xy) * bounds.w, 0.0, 1.0);
            o.col = float3(0.35, 0.78, 0.96);
            return o;
        }
        fragment float4 iw5_frag(Out in [[stage_in]]) { return float4(in.col, 1); }
        """
        do {
            let lib = try device.makeLibrary(source: source, options: nil)
            let desc = MTLRenderPipelineDescriptor()
            desc.vertexFunction = lib.makeFunction(name: "iw5_vert")
            desc.fragmentFunction = lib.makeFunction(name: "iw5_frag")
            desc.colorAttachments[0].pixelFormat = colorPixelFormat
            pipeline = try device.makeRenderPipelineState(descriptor: desc)
        } catch {
            print("IW5 preview Metal pipeline error: \(error)")
        }
        delegate = self
    }

    private var meshBounds = SIMD4<Float>(0, 0, 0, 1)

    func loadIWM1(url: URL) throws {
        guard let device = device else { throw NSError(domain: "IW5Preview", code: 1) }
        let data = try Data(contentsOf: url)
        guard data.count >= 8, Array(data.prefix(4)) == Array("IWM1".utf8) else {
            throw NSError(domain: "IW5Preview", code: 2)
        }
        let count = (UInt32(data[4]) | UInt32(data[5]) << 8 |
                     UInt32(data[6]) << 16 | UInt32(data[7]) << 24)
        guard count > 0, count <= 5_000_000, data.count == 8 + Int(count) * 12 else {
            throw NSError(domain: "IW5Preview", code: 3)
        }
        var minXY = SIMD2<Float>(repeating: Float.greatestFiniteMagnitude)
        var maxXY = SIMD2<Float>(repeating: -Float.greatestFiniteMagnitude)
        // Safe unaligned float decoding from the little-endian stream.
        for i in 0..<Int(count) {
            let offset = 8 + i * 12
            var xy = SIMD2<Float>(repeating: 0)
            for j in 0..<2 {
                let k = offset + j * 4
                let bits = UInt32(data[k]) | UInt32(data[k+1]) << 8 |
                           UInt32(data[k+2]) << 16 | UInt32(data[k+3]) << 24
                xy[j] = Float(bitPattern: bits)
                if !xy[j].isFinite { throw NSError(domain: "IW5Preview", code: 4) }
            }
            minXY = min(minXY, xy)
            maxXY = max(maxXY, xy)
        }
        let extent = max(maxXY.x - minXY.x, maxXY.y - minXY.y)
        meshBounds = SIMD4<Float>((minXY.x + maxXY.x) * 0.5,
                               (minXY.y + maxXY.y) * 0.5, 0,
                               extent > 0 ? 1.8 / extent : 1)
        meshBuffer = data.withUnsafeBytes { ptr -> MTLBuffer? in
            guard let base = ptr.baseAddress else { return nil }
            return device.makeBuffer(bytes: base.advanced(by: 8), length: data.count - 8, options: [])
        }
        vertexCount = Int(count)
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}
    func draw(in view: MTKView) {
        guard let drawable = currentDrawable, let pass = currentRenderPassDescriptor,
              let queue, let pipeline, let meshBuffer, vertexCount > 0,
              let cmd = queue.makeCommandBuffer(),
              let enc = cmd.makeRenderCommandEncoder(descriptor: pass) else { return }
        enc.setRenderPipelineState(pipeline)
        enc.setVertexBuffer(meshBuffer, offset: 0, index: 0)
        var state = meshBounds
        enc.setVertexBytes(&state, length: MemoryLayout<SIMD4<Float>>.stride, index: 1)
        enc.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: vertexCount)
        enc.endEncoding()
        cmd.present(drawable)
        cmd.commit()
    }
}
