using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.Direct3D;
using SharpDX.Direct3D11;
using SharpDX.WIC;
using System;

namespace MgsFontGenDX
{
    public abstract class RendererBase : IDisposable
    {
        private SharpDX.Direct2D1.Device _d2dDevice;
        private SharpDX.Direct2D1.Factory1 _d2dFactory;

        public RendererBase()
        {
            Initialize();
        }

        protected SharpDX.Direct2D1.DeviceContext DeviceContext { get; private set; }
        protected ImageEncoder WicImageEncoder { get; private set; }

        protected SharpDX.DirectWrite.Factory1 DWriteFactory { get; private set; }
        protected ImagingFactory2 WicFactory { get; private set; }

        protected SharpDX.Direct2D1.PixelFormat DevicePixelFormat { get; private set; }
        protected Guid ImagePixelFormat { get; private set; }

        private void Initialize()
        {
            _d2dFactory = new SharpDX.Direct2D1.Factory1();
            DWriteFactory = new SharpDX.DirectWrite.Factory1();
            WicFactory = new ImagingFactory2();

            DevicePixelFormat = new SharpDX.Direct2D1.PixelFormat(SharpDX.DXGI.Format.R8G8B8A8_UNorm, AlphaMode.Premultiplied);
            ImagePixelFormat = SharpDX.WIC.PixelFormat.Format32bppPRGBA;
            using (var defaultDevice = new SharpDX.Direct3D11.Device(DriverType.Hardware, DeviceCreationFlags.BgraSupport))
            using (var d3dDevice = defaultDevice.QueryInterface<SharpDX.Direct3D11.Device1>())
            using (var dxgiDevice = d3dDevice.QueryInterface<SharpDX.DXGI.Device2>())
            {
                _d2dDevice = new SharpDX.Direct2D1.Device(_d2dFactory, dxgiDevice);
                DeviceContext = new SharpDX.Direct2D1.DeviceContext(_d2dDevice, new DeviceContextOptions());
            }
           
            WicImageEncoder = new ImageEncoder(WicFactory, _d2dDevice);
            DeviceContext.TextAntialiasMode = SharpDX.Direct2D1.TextAntialiasMode.Grayscale;
        }

        public virtual void Dispose()
        {
            _d2dFactory?.Dispose();
            DWriteFactory?.Dispose();
            WicFactory?.Dispose();
            DeviceContext?.Dispose();
            _d2dDevice?.Dispose();
        }
    }
}
