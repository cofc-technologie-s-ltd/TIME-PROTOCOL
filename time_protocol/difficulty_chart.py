"""
TIME Protocol - Difficulty Chart (SVG)
Generates inline SVG charts for difficulty and block time.
"""


def generate_difficulty_chart(chain, width: int = 800, height: int = 300) -> str:
    """
    Generate an SVG chart showing difficulty over time.
    Returns SVG markup as a string.
    """
    if len(chain) < 2:
        return _empty_chart(width, height, "Not enough blocks yet")
    
    # Extract data
    blocks = chain[-200:]  # Last 200 blocks
    difficulties = [b.difficulty for b in blocks]
    indices = [b.index for b in blocks]
    
    # Chart dimensions
    padding_left = 60
    padding_right = 30
    padding_top = 30
    padding_bottom = 40
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom
    
    # Data ranges
    min_x = min(indices)
    max_x = max(indices) or min_x + 1
    min_y = 0
    max_y = max(difficulties) + 1
    
    if max_x == min_x:
        max_x = min_x + 1
    
    # Map data to SVG coordinates
    def x_coord(idx):
        return padding_left + (idx - min_x) / (max_x - min_x) * plot_width
    
    def y_coord(diff):
        return padding_top + plot_height - (diff - min_y) / (max_y - min_y) * plot_height
    
    # Build path
    points = [(x_coord(i), y_coord(d)) for i, d in zip(indices, difficulties)]
    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    
    # Build grid lines
    grid_lines = []
    for i in range(0, max_y + 1):
        y = y_coord(i)
        grid_lines.append(f'<line x1="{padding_left}" y1="{y:.1f}" x2="{width-padding_right}" y2="{y:.1f}" stroke="#2d3561" stroke-width="1" stroke-dasharray="2,4"/>')
        grid_lines.append(f'<text x="{padding_left-10}" y="{y+4:.1f}" fill="#8892b0" font-size="11" text-anchor="end">{i}</text>')
    
    # X-axis labels
    x_labels = []
    step = max(1, (max_x - min_x) // 6)
    for i in range(min_x, max_x + 1, step):
        x = x_coord(i)
        x_labels.append(f'<text x="{x:.1f}" y="{height-padding_bottom+20}" fill="#8892b0" font-size="11" text-anchor="middle">#{i}</text>')
    
    # Current difficulty annotation
    current_diff = difficulties[-1]
    last_x, last_y = points[-1]
    annotation = f'''
    <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="5" fill="#4a9eff"/>
    <text x="{last_x:.1f}" y="{last_y-12:.1f}" fill="#4a9eff" font-size="12" text-anchor="end" font-weight="600">
        Difficulty: {current_diff}
    </text>
    '''
    
    grid_svg = "\n".join(grid_lines)
    labels_svg = "\n".join(x_labels)
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="20" fill="#e0e6ed" font-size="14" text-anchor="middle" font-weight="600">Difficulty Over Time</text>
        {grid_svg}
        <path d="{path_d}" fill="none" stroke="#4a9eff" stroke-width="2"/>
        {labels_svg}
        {annotation}
    </svg>'''
    
    return svg


def generate_blocktime_chart(chain, width: int = 800, height: int = 250) -> str:
    """Generate SVG chart of block times."""
    if len(chain) < 3:
        return _empty_chart(width, height, "Not enough blocks")
    
    blocks = chain[-100:]
    times = []
    for i in range(1, len(blocks)):
        delta = blocks[i].timestamp - blocks[i-1].timestamp
        times.append(delta)
    
    padding_left = 60
    padding_right = 30
    padding_top = 30
    padding_bottom = 40
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom
    
    max_time = max(times) if times else 1.0
    
    # Bars
    bar_width = plot_width / len(times) if times else 0
    bars = []
    for i, t in enumerate(times):
        bar_h = (t / max_time) * plot_height
        x = padding_left + i * bar_width
        y = padding_top + plot_height - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width-1:.1f}" height="{bar_h:.1f}" fill="#4a9eff" opacity="0.7"/>')
    
    avg_time = sum(times) / len(times) if times else 0
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="20" fill="#e0e6ed" font-size="14" text-anchor="middle" font-weight="600">Block Times (last {len(times)} blocks)</text>
        <line x1="{padding_left}" y1="{padding_top + plot_height}" x2="{width-padding_right}" y2="{padding_top + plot_height}" stroke="#2d3561" stroke-width="2"/>
        <text x="{padding_left-10}" y="{padding_top+15}" fill="#8892b0" font-size="11" text-anchor="end">{max_time:.1f}s</text>
        <text x="{padding_left-10}" y="{padding_top+plot_height}" fill="#8892b0" font-size="11" text-anchor="end">0s</text>
        {''.join(bars)}
        <text x="{width//2}" y="{height-10}" fill="#8892b0" font-size="12" text-anchor="middle">Avg: {avg_time:.3f}s</text>
    </svg>'''
    
    return svg


def _empty_chart(width: int, height: int, message: str) -> str:
    return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(15,23,42,0.5); border-radius: 12px;">
        <text x="{width//2}" y="{height//2}" fill="#8892b0" font-size="14" text-anchor="middle">{message}</text>
    </svg>'''
