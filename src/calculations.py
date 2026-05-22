import math

def get_bounding_box(points):
    """
    Zwraca współrzędne prostokąta ograniczającego:
    (min_x, min_y, max_x, max_y)
    """
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)

def cross_product(o, a, b):
    """
    Iloczyn wektorowy (2D cross product) wektorów OA i OB.
    Zwraca:
    > 0 jeśli skręt w lewo
    < 0 jeśli skręt w prawo
    = 0 jeśli punkty współliniowe
    """
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def distance_sq(p1, p2):
    """Kwadrat odległości euklidesowej"""
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

def graham_scan(points):
    """
    Implementacja algorytmu Grahama do znajdowania otoczki wypukłej.
    Przyjmuje listę krotek (x, y).
    Zwraca listę punktów tworzących otoczkę (w kolejności).
    """
    if len(points) < 3:
        return points  # Otoczka nie istnieje dla < 3 punktów, zwracamy same punkty

    # 1. Znajdź punkt startowy (najniższy Y, potem najniższy X)
    start_point = min(points, key=lambda p: (p[1], p[0]))

    # 2. Sortowanie punktów względem kąta biegunowego od punktu startowego
    # Używamy atan2 dla uproszczenia
    def slope_key(p):
        if p == start_point:
            return -math.inf, 0 # Punkt startowy zawsze pierwszy
        angle = math.atan2(p[1] - start_point[1], p[0] - start_point[0])
        dist = distance_sq(start_point, p)
        return angle, dist

    sorted_points = sorted(points, key=slope_key)

    # Usuwanie duplikatów kątowych (zostawiamy ten najdalszy)
    # W prostszej wersji pythona atan2 wystarczy, ale dla precyzji:
    clean_points = [start_point]
    for i in range(1, len(sorted_points)):
        # Jeśli kąt jest inny niż poprzedniego punktu, dodaj
        # Jeśli ten sam, weź dalszy (sortowanie po dist załatwia sprawę - ostatni jest najdalszy)
        p_curr = sorted_points[i]
        p_prev = sorted_points[i-1]
        
        angle_curr = math.atan2(p_curr[1] - start_point[1], p_curr[0] - start_point[0])
        angle_prev = math.atan2(p_prev[1] - start_point[1], p_prev[0] - start_point[0])
        
        if i == 1 or not math.isclose(angle_curr, angle_prev):
            clean_points.append(p_curr)
        else:
            clean_points[-1] = p_curr

    # 3. Budowanie otoczki na stosie
    stack = [clean_points[0], clean_points[1], clean_points[2]]

    for i in range(3, len(clean_points)):
        while len(stack) > 1 and cross_product(stack[-2], stack[-1], clean_points[i]) <= 0:
            stack.pop()
        stack.append(clean_points[i])

    # Zamknięcie otoczki (dodanie punktu startowego na koniec dla rysowania)
    stack.append(stack[0])
    
    return stack