"""
Signal. Instagram Carousel Generator
Produces 8 slides (1080x1080px) ready for Instagram, LinkedIn, TikTok slideshow
"""

from PIL import Image, ImageDraw, ImageFont
import os, textwrap, math

# ── PATHS ──────────────────────────────────────────────────────────────────
import os as _os
_FONT_DIR = _os.path.join(_os.path.expanduser('~'), 'aperture', 'fonts')
FONTS = {
    'serif':      _os.path.join(_FONT_DIR, 'Lora-Bold.ttf'),
    'bold':       _os.path.join(_FONT_DIR, 'Poppins-Bold.ttf'),
    'medium':     _os.path.join(_FONT_DIR, 'Poppins-Regular.ttf'),
    'regular':    _os.path.join(_FONT_DIR, 'Poppins-Regular.ttf'),
    'mono':       _os.path.join(_FONT_DIR, 'RobotoMono-Regular.ttf'),
}

# ── PALETTE ────────────────────────────────────────────────────────────────
C = {
    'bg':        '#0A0A0F',
    'bg2':       '#12121A',
    'gold':      '#C9A84C',
    'gold_dim':  '#8B6F2E',
    'green':     '#3ECF8E',
    'red':       '#E05252',
    'orange':    '#E07B39',
    'white':     '#F0EDE6',
    'grey1':     '#8A8A9A',
    'grey2':     '#3A3A4A',
    'grey3':     '#1E1E2A',
}

W, H = 1080, 1080
PAD = 72

def font(name, size):
    return ImageFont.truetype(FONTS[name], size)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def score_color(score):
    if score <= 4:  return C['green']
    if score <= 8:  return C['gold']
    if score <= 12: return C['orange']
    return C['red']

def score_label(score):
    if score <= 4:  return "LOW RISK"
    if score <= 8:  return "ELEVATED"
    if score <= 12: return "HIGH RISK"
    return "CRISIS"

def new_canvas():
    img = Image.new('RGB', (W, H), C['bg'])
    draw = ImageDraw.Draw(img)
    return img, draw

def draw_gradient_bar(draw, x, y, w, h, score, max_score=16):
    """Horizontal score progress bar with gradient fill"""
    # Track
    draw.rounded_rectangle([x, y, x+w, y+h], radius=h//2, fill=C['grey3'])
    # Fill
    fill_w = int((score / max_score) * w)
    if fill_w > h:
        color = score_color(score)
        draw.rounded_rectangle([x, y, x+fill_w, y+h], radius=h//2, fill=color)
    # Tick marks
    for tick_score, label in [(4,''), (8,''), (12,'')]:
        tx = x + int((tick_score / max_score) * w)
        draw.rectangle([tx-1, y-4, tx+1, y+h+4], fill=C['grey2'])

def draw_noise_texture(draw, alpha=12):
    """Subtle grain texture for depth"""
    import random
    random.seed(42)
    for _ in range(8000):
        x = random.randint(0, W)
        y = random.randint(0, H)
        v = random.randint(180, 255)
        a = random.randint(0, alpha)
        draw.point([x, y], fill=(v, v, v))

def draw_brand(draw, slide_num, total=8):
    """Top bar: brand + slide counter"""
    # Brand
    f = font('bold', 28)
    draw.text((PAD, 44), "SIGNAL", font=f, fill=C['gold'])
    draw.text((PAD + 108, 44), ".", font=f, fill=C['white'])
    
    # Slide counter dots
    dot_r = 5
    dot_spacing = 18
    total_w = (total - 1) * dot_spacing + dot_r * 2
    start_x = W - PAD - total_w
    for i in range(total):
        cx = start_x + i * dot_spacing + dot_r
        cy = 58
        if i == slide_num - 1:
            draw.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r], fill=C['gold'])
        else:
            draw.ellipse([cx-dot_r+1, cy-dot_r+1, cx+dot_r-1, cy+dot_r-1], 
                        outline=C['grey2'], fill=None)

def draw_bottom_cta(draw, text="swipe for insights →"):
    """Bottom CTA"""
    f = font('medium', 22)
    bbox = draw.textbbox((0,0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 56), text, font=f, fill=C['grey1'])

def wrap_text(text, max_chars):
    """Wrap text to max chars per line"""
    return textwrap.wrap(text, width=max_chars)

def draw_multiline(draw, lines, x, y, fnt, fill, line_height=None):
    """Draw multiple lines, return final y position"""
    if line_height is None:
        bbox = draw.textbbox((0,0), "Ag", font=fnt)
        line_height = int((bbox[3] - bbox[1]) * 1.45)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_height
    return y

# ────────────────────────────────────────────────────────────────────────────
# SLIDE GENERATORS
# ────────────────────────────────────────────────────────────────────────────

def slide_1_score_reveal(data):
    """THE HOOK — Big score reveal"""
    img, draw = new_canvas()
    draw_noise_texture(draw, 8)
    
    score = data['score']
    color = score_color(score)
    label = score_label(score)
    date  = data['date']
    
    # Subtle radial glow behind score
    for r in range(220, 0, -20):
        alpha = int(18 * (1 - r/220))
        rgb = hex_to_rgb(color)
        glow_color = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        draw.ellipse([W//2 - r, 380 - r, W//2 + r, 380 + r], 
                    fill=None, outline=glow_color)
    
    draw_brand(draw, 1)
    
    # Date
    f_date = font('regular', 24)
    draw.text((PAD, 120), date.upper(), font=f_date, fill=C['grey1'])
    
    # "TODAY'S RISK SCORE"
    f_label = font('medium', 26)
    label_text = "TODAY'S RISK SCORE"
    bbox = draw.textbbox((0,0), label_text, font=f_label)
    lw = bbox[2] - bbox[0]
    draw.text(((W - lw)//2, 240), label_text, font=f_label, fill=C['grey1'])
    
    # BIG NUMBER
    f_score = font('bold', 220)
    score_str = str(score)
    bbox = draw.textbbox((0,0), score_str, font=f_score)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw)//2, 270), score_str, font=f_score, fill=color)
    
    # "/16"
    f_max = font('regular', 52)
    max_str = "/ 16"
    bbox = draw.textbbox((0,0), max_str, font=f_max)
    mw = bbox[2] - bbox[0]
    draw.text(((W - mw)//2, 530), max_str, font=f_max, fill=C['grey1'])
    
    # Score bar
    draw_gradient_bar(draw, PAD, 640, W - PAD*2, 12, score)
    
    # Labels under bar
    f_bar = font('regular', 18)
    for val, lbl in [(0,'CLEAR'), (4,'WATCH'), (8,'REDUCE'), (12,'EXIT'), (16,'CRISIS')]:
        bx = PAD + int((val/16) * (W - PAD*2))
        bbox = draw.textbbox((0,0), lbl, font=f_bar)
        bw = bbox[2] - bbox[0]
        draw.text((bx - bw//2, 666), lbl, font=f_bar, fill=C['grey2'])
    
    # Status badge
    badge_w, badge_h = 220, 52
    bx = (W - badge_w) // 2
    by = 730
    draw.rounded_rectangle([bx, by, bx+badge_w, by+badge_h], radius=8, fill=C['grey3'])
    draw.rounded_rectangle([bx, by, bx+badge_w, by+badge_h], radius=8, outline=color, width=2)
    f_badge = font('bold', 22)
    bbox = draw.textbbox((0,0), label, font=f_badge)
    lw = bbox[2] - bbox[0]
    draw.text(((W - lw)//2, by + 14), label, font=f_badge, fill=color)
    
    # Verdict (1 line)
    verdict = data.get('verdict', 'Markets hold above all key levels.')
    f_v = font('regular', 30)
    lines = wrap_text(verdict, 36)[:2]
    y = 830
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=f_v)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw)//2, y), line, font=f_v, fill=C['white'])
        y += 44
    
    draw_bottom_cta(draw, "swipe to see what's driving this  →")
    return img


def slide_2_pillars(data):
    """4 PILLAR BREAKDOWN"""
    img, draw = new_canvas()
    draw_noise_texture(draw, 6)
    draw_brand(draw, 2)
    
    # Title
    f_title = font('bold', 44)
    draw.text((PAD, 118), "Score Breakdown", font=f_title, fill=C['white'])
    
    f_sub = font('regular', 26)
    draw.text((PAD, 174), "4 pillars · 16 signals total", font=f_sub, fill=C['grey1'])
    
    # Horizontal divider
    draw.rectangle([PAD, 218, W-PAD, 220], fill=C['grey3'])
    
    pillars = data['pillars']  # list of {name, icon, score, max, status}
    
    card_w = (W - PAD*2 - 20) // 2
    card_h = 200
    
    positions = [
        (PAD, 250),
        (PAD + card_w + 20, 250),
        (PAD, 470),
        (PAD + card_w + 20, 470),
    ]
    
    status_colors = {'clear': C['green'], 'warn': C['gold'], 'danger': C['red']}
    
    for i, (pillar, (px, py)) in enumerate(zip(pillars, positions)):
        color = status_colors.get(pillar['status'], C['grey1'])
        
        # Card background
        draw.rounded_rectangle([px, py, px+card_w, py+card_h], radius=12, fill=C['grey3'])
        # Left accent bar
        draw.rounded_rectangle([px, py, px+4, py+card_h], radius=2, fill=color)
        
        # Icon + Name
        f_icon = font('bold', 36)
        draw.text((px+22, py+20), pillar['icon'], font=f_icon, fill=C['white'])
        
        f_name = font('medium', 22)
        draw.text((px+22, py+66), pillar['name'].upper(), font=f_name, fill=C['grey1'])
        
        # Score
        score_str = f"{pillar['score']}"
        max_str = f"/{pillar['max']}"
        
        f_ps = font('bold', 64)
        f_pm = font('regular', 28)
        
        bbox = draw.textbbox((0,0), score_str, font=f_ps)
        sw = bbox[2] - bbox[0]
        draw.text((px+22, py+98), score_str, font=f_ps, fill=color)
        draw.text((px+22+sw+4, py+122), max_str, font=f_pm, fill=C['grey1'])
        
        # Mini bar
        bar_x = px + 22
        bar_y = py + 174
        bar_w = card_w - 44
        draw.rounded_rectangle([bar_x, bar_y, bar_x+bar_w, bar_y+8], 
                               radius=4, fill=C['grey2'])
        fill_w = int((pillar['score'] / pillar['max']) * bar_w) if pillar['max'] else 0
        if fill_w > 4:
            draw.rounded_rectangle([bar_x, bar_y, bar_x+fill_w, bar_y+8], 
                                   radius=4, fill=color)
    
    # Bottom summary
    score = data['score']
    color = score_color(score)
    f_sum = font('medium', 28)
    summary = f"Total: {score}/16 · {score_label(score)}"
    bbox = draw.textbbox((0,0), summary, font=f_sum)
    sw = bbox[2] - bbox[0]
    draw.text(((W-sw)//2, 710), summary, font=f_sum, fill=color)
    
    # Key insight teaser
    f_teaser = font('regular', 26)
    teaser = "Swipe to see today's top 5 market insights"
    bbox = draw.textbbox((0,0), teaser, font=f_teaser)
    tw = bbox[2] - bbox[0]
    draw.text(((W-tw)//2, 762), teaser, font=f_teaser, fill=C['grey1'])
    
    draw_bottom_cta(draw)
    return img


def slide_insight(data, insight_index, slide_num):
    """INSIGHT SLIDE (slides 3-7)"""
    img, draw = new_canvas()
    draw_noise_texture(draw, 6)
    draw_brand(draw, slide_num)
    
    insights = data['insights']
    if insight_index >= len(insights):
        return None
    
    ins = insights[insight_index]
    num = insight_index + 1
    
    # Big insight number (decorative)
    f_bignum = font('bold', 180)
    draw.text((W - 160, 80), str(num), font=f_bignum, fill=C['grey3'])
    
    # "INSIGHT #N" label
    f_label = font('medium', 22)
    label = f"INSIGHT  {num} OF 5"
    draw.text((PAD, 120), label, font=f_label, fill=C['gold'])
    
    # Gold accent line
    draw.rectangle([PAD, 158, PAD+60, 163], fill=C['gold'])
    
    # Title
    f_title = font('bold', 42)
    title_lines = wrap_text(ins['title'], 28)[:3]
    y = 188
    for line in title_lines:
        draw.text((PAD, y), line, font=f_title, fill=C['white'])
        y += 56
    
    y += 16  # gap
    
    # Divider
    draw.rectangle([PAD, y, W-PAD, y+2], fill=C['grey3'])
    y += 24
    
    # Body text
    f_body = font('regular', 28)
    body_lines = wrap_text(ins['body'], 38)[:7]
    for line in body_lines:
        draw.text((PAD, y), line, font=f_body, fill=C['grey1'])
        y += 44
    
    y += 20
    
    # Tag pill
    tag = ins.get('tag', '').split('|')[0].strip().upper()
    if tag:
        f_tag = font('medium', 20)
        bbox = draw.textbbox((0,0), tag, font=f_tag)
        tw = bbox[2] - bbox[0]
        pill_pad = 16
        pill_w = tw + pill_pad * 2
        pill_h = 36
        draw.rounded_rectangle([PAD, y, PAD+pill_w, y+pill_h], 
                               radius=pill_h//2, fill=C['grey3'])
        draw.text((PAD+pill_pad, y+8), tag, font=f_tag, fill=C['gold'])
    
    # Score reminder (bottom right)
    score = data['score']
    color = score_color(score)
    f_score_sm = font('bold', 32)
    score_str = f"{score}/16"
    bbox = draw.textbbox((0,0), score_str, font=f_score_sm)
    sw = bbox[2] - bbox[0]
    draw.text((W - PAD - sw, H - 100), score_str, font=f_score_sm, fill=color)
    f_score_lbl = font('regular', 20)
    lbl = "risk score"
    bbox = draw.textbbox((0,0), lbl, font=f_score_lbl)
    lw = bbox[2] - bbox[0]
    draw.text((W - PAD - lw, H - 64), lbl, font=f_score_lbl, fill=C['grey1'])
    
    if insight_index < 4:
        draw_bottom_cta(draw, f"insight {num+1} of 5  →")
    else:
        draw_bottom_cta(draw, "swipe for the bottom line  →")
    
    return img


def slide_8_bottom_line(data):
    """FINAL SLIDE — Bottom line + CTA"""
    img, draw = new_canvas()
    draw_noise_texture(draw, 8)
    draw_brand(draw, 8)
    
    score = data['score']
    color = score_color(score)
    
    # "THE BOTTOM LINE"
    f_label = font('medium', 26)
    draw.text((PAD, 120), "THE BOTTOM LINE", font=f_label, fill=C['gold'])
    draw.rectangle([PAD, 158, W-PAD, 161], fill=C['grey3'])
    
    # Bottom line text (large, impactful)
    f_bl = font('serif', 46)
    bl_text = data.get('bottom_line', f'Score: {score}/16. Stay alert.')
    lines = wrap_text(bl_text, 26)[:5]
    y = 190
    for line in lines:
        draw.text((PAD, y), line, font=f_bl, fill=C['white'])
        y += 64
    
    y += 30
    
    # Key levels box
    draw.rounded_rectangle([PAD, y, W-PAD, y+160], radius=12, fill=C['grey3'])
    draw.rounded_rectangle([PAD, y, W-PAD, y+160], radius=12, outline=color, width=2)
    
    f_kl_title = font('medium', 22)
    draw.text((PAD+24, y+18), "KEY LEVELS TO WATCH", font=f_kl_title, fill=color)
    
    f_kl = font('regular', 26)
    levels = data.get('key_levels', [
        f"IWM 200MA: ${data['market_data'].get('ma200', 221)}",
        f"IWM 50MA: ${data['market_data'].get('ma50', 244)}",
        f"VIX: {data['market_data'].get('vix', 19.6)} (watch >25)"
    ])
    ky = y + 52
    for lvl in levels[:3]:
        draw.text((PAD+24, ky), f"→  {lvl}", font=f_kl, fill=C['white'])
        ky += 36
    
    y += 200
    
    # CTA box
    cta_y = y
    draw.rounded_rectangle([PAD, cta_y, W-PAD, cta_y+130], radius=14, fill=color)
    
    f_cta1 = font('bold', 30)
    cta1 = "Get the full daily analysis"
    bbox = draw.textbbox((0,0), cta1, font=f_cta1)
    cw = bbox[2] - bbox[0]
    draw.text(((W-cw)//2, cta_y+18), cta1, font=f_cta1, fill=C['bg'])
    
    f_cta2 = font('medium', 24)
    cta2 = "signal-intelligence.com"
    bbox = draw.textbbox((0,0), cta2, font=f_cta2)
    cw = bbox[2] - bbox[0]
    draw.text(((W-cw)//2, cta_y+60), cta2, font=f_cta2, fill=C['bg'])
    
    f_cta3 = font('regular', 20)
    cta3 = "Link in bio  ·  Free trial available"
    bbox = draw.textbbox((0,0), cta3, font=f_cta3)
    cw = bbox[2] - bbox[0]
    draw.text(((W-cw)//2, cta_y+96), cta3, font=f_cta3, fill=C['bg'])
    
    return img


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────

def generate_carousel(data: dict, output_dir: str = '/tmp/carousel') -> list[str]:
    """
    Generate all 8 carousel slides.
    
    data dict needs:
      score, date, verdict, bottom_line, pillars, insights, market_data
    
    Returns list of file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    
    slides = [
        ('01_score_reveal',   slide_1_score_reveal(data)),
        ('02_pillars',        slide_2_pillars(data)),
        ('03_insight_1',      slide_insight(data, 0, 3)),
        ('04_insight_2',      slide_insight(data, 1, 4)),
        ('05_insight_3',      slide_insight(data, 2, 5)),
        ('06_insight_4',      slide_insight(data, 3, 6)),
        ('07_insight_5',      slide_insight(data, 4, 7)),
        ('08_bottom_line',    slide_8_bottom_line(data)),
    ]
    
    for name, img in slides:
        if img is None:
            continue
        path = os.path.join(output_dir, f'signal_{name}.png')
        img.save(path, 'PNG', quality=95)
        paths.append(path)
        print(f"  ✓ {name}")
    
    return paths


# ── TEST DATA ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    test_data = {
        'score': 2,
        'date': 'Friday, February 27, 2026',
        'verdict': 'Markets hold firm above all key levels. No crisis signal active.',
        'bottom_line': 'Score 2/16. Golden Cross intact, credit markets calm. Watch PCE today and ISM on March 2. Bias remains: stay invested.',
        'key_levels': [
            'IWM 200MA: $221 — primary support',
            'IWM 50MA: $244 — must hold on pullback',
            'VIX >25 = re-score trigger',
        ],
        'market_data': {
            'iwm_price': 264.28,
            'ma50': 243.95,
            'ma200': 221.23,
            'vix': 19.62,
            'hy_spread': 2.95,
            'yield_curve_spread': 0.60,
            'iwm_vs_200ma_pct': 19.5,
        },
        'pillars': [
            {'name': 'Technical',  'icon': '📊', 'score': 0, 'max': 5, 'status': 'clear'},
            {'name': 'Breadth',    'icon': '🌊', 'score': 0, 'max': 4, 'status': 'clear'},
            {'name': 'Macro',      'icon': '🏛', 'score': 1, 'max': 5, 'status': 'warn'},
            {'name': 'Sentiment',  'icon': '🧠', 'score': 1, 'max': 4, 'status': 'warn'},
        ],
        'insights': [
            {
                'title': "ISM's 52.6 reading is a genuine turning point",
                'body': "After 26 consecutive months of contraction, US manufacturing expanded in January — the longest drought since 2008-09. New orders jumped to 57.1, highest since Feb 2022. Small caps are the primary beneficiary when manufacturing turns: 77% of Russell 2000 revenue is domestic.",
                'tag': 'Manufacturing · Bullish for IWM',
            },
            {
                'title': 'Golden Cross intact — but watch momentum',
                'body': "The 50-day MA ($244) remains above the 200-day MA ($221). Every sustained IWM bull run occurred with Golden Cross active. One caveat: momentum indicators softened even as price held. Divergence (strong price, weakening momentum) is a yellow flag for the next 2-3 weeks.",
                'tag': 'Technical · Watch',
            },
            {
                'title': 'Credit markets are the cleanest all-clear signal',
                'body': "High yield spreads at 2.95% are near 5-year tights. The corporate bond market is pricing essentially zero financial stress. In every major IWM crisis, HY spreads blew out to 500-800bps BEFORE stocks cracked. Current spreads say: no systemic risk on the horizon.",
                'tag': 'Credit · Very Bullish',
            },
            {
                'title': 'The Warsh transition is the one unknown',
                'body': "Kevin Warsh replaces Powell in May 2026. As a \"sound money\" advocate he may be less dovish. Small caps carry 32% floating-rate debt vs 6% for large caps. A hawkish surprise from new Fed chair could disproportionately hit Russell 2000. Tail risk, not base case.",
                'tag': 'Fed Policy · Tail Risk',
            },
            {
                'title': 'Tariff noise is back — market has learned to discount it',
                'body': "Supreme Court struck IEEPA tariffs, Trump responded with 10% blanket tariff. IWM barely moved. Compare to April 2025 when tariff shock sent IWM down 25%. Reduced sensitivity suggests risk is partially priced in — but sector-specific escalation could still sting.",
                'tag': 'Trade Policy · Priced In',
            },
        ],
    }

    print("\nGenerating Signal. carousel slides...\n")
    paths = generate_carousel(test_data, '/tmp/carousel')
    print(f"\n✓ {len(paths)} slides generated")
    for p in paths:
        size = os.path.getsize(p) // 1024
        print(f"  {os.path.basename(p)}  ({size}KB)")
