# exploded-stack
**Use for:** "how it works", architecture, layers of a product, the ingredients of an offer, "built on".  **Length:** 3–4.5 s
**Needs:** 3–5 layer names (bottom → top), each 1–2 words.
**Beats**
- 0.2–1.2: the layers drop in bottom-up (staggered 0.2 s, `back.out(1.6)`); each layer's mono tag slides in beside it right after
- 1.6–2.8: the stack spreads apart: each layer and its tag rise by an even extra gap (`sine.inOut`)
- The key layer (usually the brand's own, on top) carries the brand colour and a highlighted tag
- Variant: draw leader lines from layer to tag (SVG `<line>` + `stroke-dashoffset`) when the tags sit far from the stack
- Hold ≥ 1 s, with a very slow float of the whole stack
**Build:** template scene S4. Flat `box` slabs (`h ≈ 0.32`, spaced 0.75 units); tag positions come from `IsoKit.P()` at each slab's right corner; labels are `.tag` HTML.
**SFX:** one stacked "tok tok tok" on landing, a soft whoosh on the explode.
**Avoid:** more than 5 layers; labels crossing each other; slabs so thin that their side faces disappear.
**Registry starting points:** none. Build from the template.
