"""
TIME Protocol - Difficulty Chart (SVG)
"""


def generate_difficulty_chart(chain, width=800, height=300):
    if len(chain) < 2:
        return _empty_chart(width, height, "Not enough blocks yet")
    
    blocks = chain[-200:]
    difficulties = [b.difficulty for b in blocks]
    indices = [b.index for b in blocks]
    
    pad_l, pad_r, pad_t, pad_b = 60, 30, 30, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    
    min_x, max_x = min(indices), max(indices) or min(indices) + 1
    min_y, max_y = 0, max(difficulties) + 1
    
    if max_x == min_x:
        max_x = min_x + 1
    
    def xc(idx):
        return pad_l + (idx - min_x) / (max_x - min_x) * plot_w
    
    def yc(d):
        return pad_t + plot_h - (d - min_y) / (max_y - min_y) * plot_h
    
    points = [(xc(i), yc(d)) for i, d in zip(indices, difficulties)]
    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    
    grid_lines = []
    for i in range(0, max_y + 1):
        y = yc(i)
        grid_lines.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-pad_r}" y2="{y:.1f}" stroke="#2d3561" stroke-dasharray="2,4"/>')
        grid_lines.append(f'<text x="{pad_l-10}" y="{y+4:.1f}" fill="#8892b0" font-size="11" text-anchor="end">{i}</text>')
    
    x_labels = []
    step = max(1, (max_x - min_x) // 6)
    for i in range(min_x, max_x + 1, step):
        x = xc(i)
        x_labels.append(f'<text x="{x:.1f}" y="{height-pad_b+20}" fill="#8892b0" font-size="11" text-anchor="middle">#{i}</text>')
    
    last_x, last_y = points[-1]
    current_diff = difficulties[-1]
    
    return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="20" fill="#e0e6ed" font-size="14" text-anchor="middle" font-weight="600">Difficulty Over Time</text>
        {"".join(grid_lines)}
        <path d="{path_d}" fill="none" stroke="#4a9eff" stroke-width="2"/>
        {"".join(x_labels)}
        <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="5" fill="#4a9eff"/>
        <text x="{last_x:.1f}" y="{last_y-12:.1f}" fill="#4a9eff" font-size="12" text-anchor="end" font-weight="600">
            Difficulty: {current_diff}
        </text>
    </svg>'''


def generate_blocktime_chart(chain, width=800, height=250):
    if len(chain) < 3:
        return _empty_chart(width, height, "Not enough blocks")
    
    blocks = chain[-100:]
    times = [blocks[i].timestamp - blocks[i-1].timestamp for i in range(1, len(blocks))]
    
    pad_l, pad_r, pad_t, pad_b = 60, 30, 30, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    
    max_time = max(times) if times else 1.0
    bar_width = plot_w / len(times) if times else 0
    
    bars = []
    for i, t in enumerate(times):
        bar_h = (t / max_time) * plot_h
        x = pad_l + i * bar_width
        y = pad_t + plot_h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width-1:.1f}" height="{bar_h:.1f}" fill="#4a9eff" opacity="0.7"/>')
    
    avg_time = sum(times) / len(times) if times else 0
    
    return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="20" fill="#e0e6ed" font-size="14" text-anchor="middle" font-weight="600">Block Times (last {len(times)} blocks)</text>
        <line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width-pad_r}" y2="{pad_t + plot_h}" stroke="#2d3561" stroke-width="2"/>
        <text x="{pad_l-10}" y="{pad_t+15}" fill="#8892b0" font-size="11" text-anchor="end">{max_time:.1f}s</text>
        <text x="{pad_l-10}" y="{pad_t+plot_h}" fill="#8892b0" font-size="11" text-anchor="end">0s</text>
        {"".join(bars)}
        <text x="{width//2}" y="{height-10}" fill="#8892b0" font-size="12" text-anchor="middle">Avg: {avg_time:.3f}s</text>
    </svg>'''


def _empty_chart(width, height, message):
    return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="{height//2}" fill="#8892b0" font-size="14" text-anchor="middle">{message}</text>
    </svg>'''
