import plotly.graph_objects as go
import textwrap


def visualize_interactive_graph(graph, edges, output_path="graph.html"):
    def draw_graph_edges(_pos, _edges):
        _graph_edges = {
            "x": [],
            "y": [],
        }

        for _edge in _edges:
            _x0, _y0 = _pos[_edge[0]]
            _x1, _y1 = _pos[_edge[1]]
            _graph_edges["x"].extend([_x0, _x1, None])
            _graph_edges["y"].extend([_y0, _y1, None])

        _edge_trace = go.Scatter(
            x=_graph_edges["x"], y=_graph_edges["y"],
            line=dict(width=1, color='gray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )

        return _edge_trace

    def draw_graph_nodes(_pos, _graph, line_len=30, width_const=0.1, height_const=0.4):
        def calc_graph_node_rectangle(_data, _line_len=30, _width_const=0.005, _height_const=0.15):
            _node_text = f"{_data['author']}({_data['source']})<br>[{_data['date']}]:<br>{_data['title']}"
            _node_rectangle = {
                "text": textwrap.fill(_node_text, width=_line_len).replace("\n", "<br>"),
                "width": float,
                "height": float
            }

            num_lines = _node_rectangle["text"].count("<br>") + 1
            _node_rectangle["width"] = _width_const * max(len(line) for line in _node_rectangle["text"].split("<br>"))
            _node_rectangle["height"] = _height_const * num_lines

            return _node_rectangle

        _graph_nodes = {
            "x": [],
            "y": [],
            "text": [],
            "shapes": [],
            "links": [],
        }

        for node, data in _graph.nodes(data=True):
            x, y = _pos[node]

            node_rectangle = calc_graph_node_rectangle(_data=data, _line_len=line_len,
                                                       _width_const=width_const, _height_const=height_const)

            _graph_nodes["x"].append(x)
            _graph_nodes["y"].append(y)
            _graph_nodes["text"].append(f"<a href='{node}' target='_blank'>{node_rectangle['text']}</a>")
            _graph_nodes["links"].append(node)

            _graph_nodes["shapes"].append(
                dict(
                    type="rect",
                    x0=x - node_rectangle["width"] / 2, y0=y - node_rectangle["height"] / 2,
                    x1=x + node_rectangle["width"] / 2, y1=y + node_rectangle["height"] / 2,
                    line=dict(color='blue'),
                    fillcolor="rgba(0,0,0,0)"
                )
            )

        _node_trace = go.Scatter(
            x=_graph_nodes["x"], y=_graph_nodes["y"],
            mode='text',
            text=_graph_nodes["text"],
            textposition="middle center",
            hoverinfo='text'
        )

        return _graph_nodes, _node_trace

    # Начальная позиция для каждого подграфа
    pos = {}
    current_x = 0
    current_y = 0
    max_width = 5  # Максимальная ширина для группы (подграфа)
    node_padding = 0.2  # Отступы для узлов

    for edge in edges:
        # Для каждого подграфа вычисляем свои позиции
        x0, y0 = current_x, current_y
        x1, y1 = current_x, current_y + 5  # Смещение для следующего подграфа
        pos[edge[0]] = (x0, y0)
        pos[edge[1]] = (x1, y1)

        # Смещаемся вправо для следующего подграфа
        current_x += max_width + 1  # Отступ между подграфами
        if current_x > 15:  # Если нет места по оси X, переносим на новую строку
            current_x = 0
            current_y += 10

    # Создание рёбер и узлов для визуализации
    edge_trace = draw_graph_edges(_pos=pos, _edges=edges)
    graph_nodes, node_trace = draw_graph_nodes(_pos=pos, _graph=graph)

    # Построение графа
    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title="Граф схожих новостей",
        title_font_size=24,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=40, l=40, r=40, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        shapes=graph_nodes["shapes"]
    )

    # fig.show()
    fig.write_html(output_path)