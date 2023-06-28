import math

class Simulator:
    def __init__(self, max_speed, max_acc, min_acc, mass):
        self.max_speed = max_speed #m/s
        self.max_acceleration = max_acc   #m/s^2
        self.min_acceleration = min_acc  #m/s^2
        self.mass = mass   #kg

        self.FRICTION_COEF = 0.1
        self.GRAV_ACCELERATION = 9.8 #m/s^2
        self.GRAVITY_FORCE = self.mass * self.GRAV_ACCELERATION

        self.Cd = 0.4 #wspolczynnik oporu powietrza
        self.A = 0.8 #pole powierzchni pojazdu

        self.velocity = [0]
        self.acceleration = [0]
        self.position = [0]
        self.time = [0]

    def print_data(self):
        print("Max Speed:", self.max_speed)
        print("Max Acceleration:", self.max_acceleration)
        print("Min Acceleration:", self.min_acceleration)
        print("Mass:", self.mass)

    def count_distance(self):
        #liczy potrzebne wartości każdego odcinka na trasie
        start = self.road[0]
        roads_length = []
        roads_cos = []
        roads_sin = []

        for element in self.road[1:]:
            roads_length_x = element[0] - start[0]
            roads_length_y = element[1] - start[1]
            roads_length.append(math.sqrt(roads_length_x**2 + roads_length_y**2))

            roads_cos.append(roads_length_x / roads_length[-1])
            roads_sin.append(roads_length_y / roads_length[-1])

            start = element

        return roads_length, roads_cos, roads_sin

    def simulate(self, road):
        
        self.road = road

        roads_length, roads_cos, roads_sin = self.count_distance()
        simulation_time = int(sum(roads_length)/self.max_speed)

        tp = simulation_time/1000
        ti = 10  #stała całkowania
        kp = .6 #wspołczynnik wzmocnienia

        u_min = 0
        u_max = 10

        tangens = (self.max_acceleration - self.min_acceleration) / (u_max - u_min)
        velocity_difference = [self.max_speed]

        current_road = 0

        while self.position[-1] < sum(roads_length):
            
            velocity_difference.append(self.max_speed - self.velocity[-1])

            #obliczenie wszystkich sił działających na ciało
            fn = self.GRAVITY_FORCE * roads_cos[current_road]       #siła nacisku
            fz = self.GRAVITY_FORCE * roads_sin[current_road]       #siła zsuwająca
            ft = fn * self.FRICTION_COEF                            #siła tarcia
            fp = 0.5 * (self.velocity[-1]**2) * self.A * self.Cd    #siła oporu powietrza

            #przyspieszenie które musi wygenerować pojazd aby utrzymać stałą prędkość
            acc = (fz + ft + fp) / self.mass

            upi = (kp * velocity_difference[-1]) + (tp * sum(velocity_difference) / ti) 
            upi = max(min(upi, u_max), u_min)
            self.acceleration.append(tangens * (upi - u_min) + self.min_acceleration)

            self.time.append(self.time[-1] + tp)
            self.position.append(self.position[-1] + (self.velocity[-1] * tp))
            self.velocity.append(self.velocity[-1] + (self.acceleration[-1] - acc) * tp)

            #sprawdzenie czy pojazd zakończył ruch na danym odcinku
            if self.position[-1] > sum(roads_length[:current_road + 1]):
                current_road += 1
                