import numpy as np
from parapy.core import *
from parapy.geom import *
from math import *

import aircraft.Import_Input as In
from aircraft.fuselage import Fuselage
from aircraft.wing import Wing
from aircraft.empennage import VerticalTail


# Class that defines location of engines and places them
class PropulsionSystem(GeomBase):
    n_engines = Input(In.N_engines)
    thrust_to = Input(In.Thrust_TO)
    bypass_ratio = Input(In.BPR)
    turbine_inlet_temp = Input(In.Temp_T_4)
    phi = Input(In.Phi)
    span = Input(Wing().span)
    diameter_fuselage_outer = Input(Fuselage().diameter_fuselage_outer)
    wing_z_shift = Input(Wing().wing_z_shift)
    dihedral = Input(Wing().dihedral)
    x_tail_vertical = Input(VerticalTail().x_tail_vertical)
    wing_x_shift = Input(Wing().wing_x_shift)
    sweep_leading_edge = Input(Wing().sweep_leading_edge)
    max_diameter = Input(2)

    # creates a list of y positions depending pn how many engines are needed
    @Attribute
    def y_pos(self):
        if self.n_engines == 1:
            pos1 = 0
            y_distr = [pos1]
        elif self.n_engines == 2:
            pos1 = 0.35 * self.span / 2
            y_distr = [-pos1, pos1]
        elif self.n_engines == 3:
            pos1 = 0.35 * self.span / 2
            pos2 = 0
            y_distr = [-pos1, pos2, pos1]
        elif self.n_engines == 4:
            pos1 = 0.4 * self.span / 2
            pos2 = 0.7 * self.span / 2
            y_distr = [-pos2, -pos1, pos1, pos2]
        return y_distr

    # creates a list of all z positions dependent on how many engines are needed
    @Attribute
    def z_pos(self):
        if self.n_engines == 1:
            pos1 = self.diameter_fuselage_outer / 2 + self.max_diameter * 1.1 / 2
            z_distr = [pos1]
        elif self.n_engines == 2:
            pos1 = self.wing_z_shift + np.tan(
                np.deg2rad(self.dihedral)) * 0.35 * self.span / 2 - self.max_diameter * 1.1 / 2
            z_distr = [pos1, pos1]
        elif self.n_engines == 3:
            pos1 = self.wing_z_shift + np.tan(
                np.deg2rad(self.dihedral)) * 0.35 * self.span / 2 - self.max_diameter * 1.1 / 2
            pos2 = self.diameter_fuselage_outer / 2 + self.max_diameter * 1.1 / 2
            z_distr = [pos1, pos2, pos1]
        elif self.n_engines == 4:
            pos1 = self.wing_z_shift + np.tan(
                np.deg2rad(self.dihedral)) * 0.4 * self.span / 2 - self.max_diameter * 1.1 / 2
            pos2 = self.wing_z_shift + np.tan(
                np.deg2rad(self.dihedral)) * 0.7 * self.span / 2 - self.max_diameter * 1.1 / 2
            z_distr = [pos2, pos1, pos1, pos2]
        return z_distr

    # creates a list of all x positions dependent on how many engines are needed
    @Attribute
    def x_pos(self):
        if self.n_engines == 1:
            pos1 = self.x_tail_vertical - 0.5
            x_distr = [pos1]
        elif self.n_engines == 2:
            pos1 = self.wing_x_shift + np.tan(np.deg2rad(self.sweep_leading_edge)) * 0.35 * self.span / 2 - 0.5
            x_distr = [pos1, pos1]
        elif self.n_engines == 3:
            pos1 = self.wing_x_shift + np.tan(np.deg2rad(self.sweep_leading_edge)) * 0.35 * self.span / 2 - 0.5
            pos2 = self.x_tail_vertical - 0.5
            x_distr = [pos1, pos2, pos1]
        elif self.n_engines == 4:
            pos1 = self.wing_x_shift + np.tan(np.deg2rad(self.sweep_leading_edge)) * 0.4 * self.span / 2 - 0.5
            pos2 = self.wing_x_shift + np.tan(np.deg2rad(self.sweep_leading_edge)) * 0.7 * self.span / 2 - 0.5
            x_distr = [pos2, pos1, pos1, pos2]
        return x_distr

    # creates multiple instances of FanEngine and places them where needed
    @Part
    def propulsion_system(self):
        return FanEngine(thrust_to=self.thrust_to,
                         n_engines=self.n_engines,
                         bypass_ratio=self.bypass_ratio,
                         turbine_inlet_temp=self.turbine_inlet_temp,
                         phi=self.phi,
                         quantify=int(self.n_engines),
                         position=translate(self.position,
                                            'x', self.x_pos[child.index],
                                            'y', self.y_pos[child.index],
                                            'z', self.z_pos[child.index]),
                         hidden=False)


# class that creates one engine
class FanEngine(GeomBase):
    n_engines = Input(In.N_engines)
    thrust_to = Input(In.Thrust_TO)
    bypass_ratio = Input(In.BPR)
    turbine_inlet_temp = Input(In.Temp_T_4)
    phi = Input(In.Phi)

    eta_n = Input(0.97)
    eta_tf = Input(0.75)
    sound_speed = Input(343)
    rho_0 = Input(1.225)

    # a lot of half-emperical relations to estimate some engine sizing parameters, relations and
    # sizing procedure stem from ADSEE1
    @Attribute
    def massflow(self):
        gg = self.turbine_inlet_temp / 600 - 1.25
        return (self.thrust_to * 10 ** 6) / (self.n_engines * self.sound_speed) * (1 + self.bypass_ratio) / (
            np.sqrt(5 * self.eta_n * gg * (1 + self.eta_tf * self.bypass_ratio)))


    @Attribute
    def ratio_inlet_to_spinner(self):
        return 0.05 * (1 + 0.1 * (self.rho_0 * self.sound_speed) / self.massflow + (3 * self.bypass_ratio) / (
                1 + self.bypass_ratio))

    @Attribute
    def inlet_diameter(self):
        return 1.65 * np.sqrt(
            (0.005 + self.massflow / (self.rho_0 * self.sound_speed)) / (1 - self.ratio_inlet_to_spinner ** 2))

    @Attribute
    def nacelle_length(self):
        if self.phi == 1:
            cl = 9.8
            delta_l = 0.05

        elif self.phi < 1:
            cl = 7.8
            delta_l = 0.1

        return cl * (delta_l + np.sqrt((self.massflow * (1 + 0.2 * self.bypass_ratio)) / (
                self.rho_0 * self.sound_speed * (1 + self.bypass_ratio))))

    @Attribute
    def fan_length(self):
        return self.phi * self.nacelle_length

    @Attribute
    def loc_max_diameter(self):
        if self.phi == 1:
            beta = 0.35
        elif self.phi < 1:
            beta = 0.21 + 0.12 / (np.sqrt(self.phi - 0.3))
        return beta

    @Attribute
    def max_diameter(self):
        return self.inlet_diameter + 0.06 * self.fan_length + 0.03

    @Attribute
    def exit_diameter(self):
        return self.max_diameter * (1 - 1 / 3 * self.phi ** 2)

    @Attribute
    def length_gas_generator(self):
        return (1 - self.phi) * self.nacelle_length

    @Attribute
    def diameter_gas_generator(self):
        lambda_m_over_a_rho = self.bypass_ratio * self.massflow / (self.rho_0 * self.sound_speed)
        return self.exit_diameter * ((0.089 * lambda_m_over_a_rho + 4.5) / (0.067 * lambda_m_over_a_rho + 5.8)) ** 2

    @Attribute
    def exit_diameter_gas_generator(self):
        return 0.55 * self.diameter_gas_generator

    # create the physical parts of the engine
    # create the spinner as a cone
    @Part
    def spinner(self):
        return Cone(radius1=0.05,
                    radius2=self.inlet_diameter * self.ratio_inlet_to_spinner,
                    height=0.5,
                    position=rotate(self.position, "y", np.deg2rad(90)),
                    color="yellow")

    # create the fan as a disc
    @Part
    def fan(self):
        return Cylinder(radius=self.inlet_diameter / 2,
                        height=self.inlet_diameter * 0.05,
                        position=translate(rotate(self.position, "y", np.deg2rad(90)), "z", 0.5),
                        color="orange")

    # create the core as a cylinder
    @Part
    def core(self):
        return Cylinder(radius=self.diameter_gas_generator / 2,
                        height=self.fan_length - 0.5 - self.inlet_diameter * 0.05,
                        position=translate(rotate(self.position, "y", np.deg2rad(90)),
                                           "z", self.inlet_diameter * 0.05 + 0.5),
                        color="orange")

    # create the nozzle as a cone
    @Part
    def nozzle(self):
        return Cone(radius1=self.diameter_gas_generator / 2,
                    radius2=self.exit_diameter_gas_generator / 2,
                    height=self.length_gas_generator,
                    position=translate(rotate(self.position, "y", np.deg2rad(90)),
                                       "z", self.fan_length),
                    color="orange")

    # create the cowling as two cones (diverging and converging)
    @Part
    def bypass_cowling_1(self):
        return Cone(radius1=(self.inlet_diameter + 0.2) / 2,
                    radius2=self.max_diameter / 2,
                    height=self.loc_max_diameter,
                    position=rotate(self.position, "y", np.deg2rad(90)),
                    hidden=True)

    @Part
    def bypass_cowling_2(self):
        return Cone(radius1=self.max_diameter / 2,
                    radius2=self.exit_diameter / 2,
                    height=self.fan_length - self.loc_max_diameter,
                    position=translate(rotate(self.position, "y", np.deg2rad(90)),
                                       "z", self.loc_max_diameter),
                    hidden=True)

    # fuse the bypass cones together
    @Part
    def fused_bypass_outer(self):
        return FusedSolid(shape_in=self.bypass_cowling_1, tool=self.bypass_cowling_2,
                          color="Orange",
                          hidden=True)

    # crete two cones, slightly smaller to cut-out the bypass  cowling
    @Part
    def bypass_cowling_cut_1(self):
        return Cone(radius1=self.inlet_diameter / 2,
                    radius2=(self.max_diameter - 0.2) / 2,
                    height=self.loc_max_diameter,
                    position=rotate(self.position, "y", np.deg2rad(90)),
                    hidden=True)

    @Part
    def bypass_cowling_cut_2(self):
        return Cone(radius1=(self.max_diameter - 0.2) / 2,
                    radius2=(self.exit_diameter - 0.2) / 2,
                    height=self.fan_length - self.loc_max_diameter,
                    position=translate(rotate(self.position, "y", np.deg2rad(90)),
                                       "z", self.loc_max_diameter),
                    hidden=True)

    # fuse the parts to cut away
    @Part
    def fused_bypass_inner(self):
        return FusedSolid(shape_in=self.bypass_cowling_cut_1,
                          tool=self.bypass_cowling_cut_2,
                          color="Orange",
                          hidden=True)

    # subtract the full bypass cowling with the inner part to create a thinner hollowed out cone
    @Part
    def bypass(self):
        return SubtractedSolid(shape_in=self.fused_bypass_outer,
                               tool=self.fused_bypass_inner,
                               color="yellow",
                               transparency=0.5)


if __name__ == '__main__':
    from parapy.gui import display

    obj1 = PropulsionSystem(label="Prop")
    display(obj1)
