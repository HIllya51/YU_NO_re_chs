using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;
using System;

namespace MgsFontGenDX
{
    public class OutlineRenderer : TextRendererBase
    {
        readonly SharpDX.Direct2D1.Factory _factory;
        readonly RenderTarget _surface;

        public OutlineRenderer(RenderTarget surface)
        {
            _factory = surface.Factory;
            _surface = surface;
        }

        public override Result DrawGlyphRun(object clientDrawingContext, float baselineOriginX, float baselineOriginY, MeasuringMode measuringMode, GlyphRun glyphRun, GlyphRunDescription glyphRunDescription, ComObject clientDrawingEffect)
        {
            using (PathGeometry path = new PathGeometry(_factory))
            using (GeometrySink sink = path.Open())
            {
                glyphRun.FontFace.GetGlyphRunOutline(glyphRun.FontSize, glyphRun.Indices, glyphRun.Advances, glyphRun.Offsets, glyphRun.IsSideways, false, sink);
                sink.Close();

                var translation = Matrix3x2.Translation(baselineOriginX, baselineOriginY);
                var outline = new TransformedGeometry(_factory, path, translation);
                using (var strokeStyle = new StrokeStyle(_factory, new StrokeStyleProperties { LineJoin = LineJoin.Round }))
                {
                    for (int i = 1; i < 8; i++)
                    {
                        var color = Color.White;
                        color.A /= (byte)Math.Ceiling(i / 1.5);
                        using (var brush = new SolidColorBrush(_surface, color))
                        {
                            _surface.DrawGeometry(outline, brush, i, strokeStyle);
                        }
                    }
                }
            }

            return new Result();
        }
    }
}
