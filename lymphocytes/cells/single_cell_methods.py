import matplotlib.pyplot as plt
import lymphocytes.utils.plotting as utils_plotting
import sys
import numpy as np
import pyvista as pv
import pickle

import lymphocytes.utils.general as utils_general


class Single_Cell_Methods:
    """
    Inherited by Cell_Frame class.
    Contains methods for series of a single cell.
    """

    def _uropod_callback(self, a, b):
        """
        Callback for when selecting uropods
        """
        point = np.array(a.points[b, :])
        print(point)
        self.uropod_coords[-1] = point

    def select_uropods(self, idx_cell):
        """
        Select the uropods
        """
        self.frames = []
        self.uropod_coords = []

        lymphs = self.cells[idx_cell]


        for idx_plot, lymph in enumerate(lymphs):
            print(idx_plot)
            self.frames.append(lymph.frame)

            plotter = pv.Plotter()

            if idx_plot == 0:
                lymph.surface_plot(plotter=plotter, uropod_align=False, opacity = 0.1, scalars = None)
            else:
                # color face closest to prev uropod (adding point at that location makes point selection snap to that point)
                dists = [np.linalg.norm(self.uropod_coords[-1]-lymph.vertices[i, :]) for i in range(lymph.vertices.shape[0])]
                idx_closest = dists.index(min(dists))
                scalars = []
                for idx in range(int(lymph.faces.shape[0]/4)):
                    if idx_closest in lymph.faces[idx*4:(idx+1)*4]:
                        scalars.append(0.5)
                    else:
                        scalars.append(0)
                lymph.surface_plot(plotter=plotter, uropod_align=False, opacity = 0.1, scalars = scalars)

            self.uropod_coords.append(None)
            plotter.enable_point_picking(callback = self._uropod_callback, show_message=True,
                       color='pink', point_size=10,
                       use_mesh=True, show_point=True)
            #plotter.enable_cell_picking(through=False, callback = self._uropod_callback)
            plotter.show(cpos=[0, 1, 0])


        uropod_dict = {frame:coords for frame, coords in zip(self.frames, self.uropod_coords)}

        pickle_out = open('/Users/harry/OneDrive - Imperial College London/lymphocytes/uropods/cell_{}.pickle'.format(idx_cell),'wb')
        pickle.dump(uropod_dict, pickle_out)
        print(uropod_dict)



    def plot_orig_series(self, idx_cell, uropod_align, color_by = None, plot_every = 1):
        """
        Plot original mesh series, with point at the uropods
        """

        lymphs_plot = self.cells[idx_cell][::plot_every]
        num_cols=int(len(lymphs_plot)/3)+1
        plotter = pv.Plotter(shape=(3, num_cols), border=False)

        if color_by is not None:
            if color_by[:3] == 'pca':
                self._set_pca(n_components=3)
            elif color_by == 'delta_centroid' or color_by == 'delta_sensing_direction':
                self._set_centroid_attributes(color_by, num_either_side = 2)
            elif color_by == 'morph_deriv':
                self._set_morph_derivs()
            vmin, vmax = utils_general.get_color_lims(self, color_by)

        for idx_plot, lymph in enumerate(lymphs_plot):
            plotter.subplot(idx_plot//num_cols, idx_plot%num_cols)
            plotter.add_text("{}".format(lymph.frame), font_size=30)
            #plotter.subplot(idx_plot, 0)

            color = (1, 1, 1)
            if color_by is not None:
                if getattr(lymph, color_by) is not None:
                    color = (1-(getattr(lymph, color_by)-vmin)/(vmax-vmin), 1, 1)
            lymph.surface_plot(plotter=plotter, uropod_align=uropod_align, color = color)

        plotter.show(cpos=[0, 1, 0])
        print('------')

    def plot_uropod_centroid_line(self, idx_cell, plot_every):

        lymphs_plot = self.cells[idx_cell][::plot_every]
        plotter = pv.Plotter()

        for idx_plot, lymph in enumerate(lymphs_plot):
            lymph.uropod_centroid_line_plot(plotter=plotter, color = (1, idx_plot/(len(lymphs_plot)-1), 1))

            plotter.add_mesh(pv.Sphere(radius=0.1, center=lymph.uropod), color = (1, 0, 0))
            plotter.add_mesh(pv.Sphere(radius=0.1, center=lymph.centroid), color = (0, 1, 0))
        plotter.show(cpos=[0, 1, 0])




    def plot_uropod_trajectory(self, idx_cell):

        fig = plt.figure()
        ax = fig.add_subplot(111, projection = '3d')
        uropods = [lymph.uropod for lymph in self.cells[idx_cell]]
        ax.plot([i[0] for i in uropods], [i[1] for i in uropods], [i[2] for i in uropods])


    def plot_migratingCell(self, idx_cell,  plot_every = 15):
        """
        Plot all meshes of a cell in one window
        """

        lymphs = self.cells[idx_cell][::plot_every]
        plotter = pv.Plotter()

        for idx_lymph, lymph in enumerate(lymphs):

            surf = pv.PolyData(lymph.vertices, lymph.faces)
            plotter.add_mesh(surf, color = (1, idx_lymph/(len(lymphs)-1), 1), opacity =  0.5)
        box = pv.Box(bounds=(0, 92.7, 0, 52.7, 0, 26.4))
        plotter.add_mesh(box, style='wireframe')
        plotter.add_axes()
        plotter.show(cpos=[0, 1, 0.5])

    def plot_attribute(self, idx_cell, attribute):

        if attribute[:3] == 'pca':
            self._set_pca(n_components=3)
        if attribute == 'delta_centroid' or attribute == 'delta_sensing_direction':
            self._set_centroid_attributes(attribute)

        lymphs = self.cells[idx_cell]
        frame_list = [lymph.frame for lymph in lymphs if getattr(lymph, attribute) is not None]
        attribute_list = [getattr(lymph, attribute) for lymph in lymphs if getattr(lymph, attribute)  is not None]

        plt.plot(frame_list, attribute_list)
        plt.show()


    def plot_series_PCs(self, idx_cell, plot_every):
        """
        Plot the PCs of each frame of a cell
        """
        fig = plt.figure(figsize = (1, 6))
        self._set_pca(n_components = 3)
        lymphs = self.cells[idx_cell][::plot_every]
        for idx, lymph in enumerate(lymphs):
            ax = fig.add_subplot(len(lymphs), 1, idx+1)
            ax.bar(range(len(lymph.pca_normalized)), lymph.pca_normalized)
            ax.set_ylim([-3.5, 3.5])
            ax.set_yticks([])
            ax.set_yticks([-3, 3])
            ax.set_xticks([])
        plt.tight_layout()
        plt.subplots_adjust(hspace = 0)
        plt.show()


    def plot_recon_series(self, idx_cell, plot_every, max_l = None, color_by = None):
        """
        Plot reconstructed mesh series
        """

        if color_by is not None:
            if color_by[:3] == 'pca':
                self._set_pca(n_components=3)
            else:
                self._set_centroid_attributes(color_by, num_either_side = 2)
            vmin, vmax = utils_general.get_color_lims(self, color_by)

        lymphs_plot = self.cells[idx_cell][::plot_every]
        num_cols = (len(lymphs_plot) // 3) + 1
        plotter = pv.Plotter(shape=(3, num_cols))
        for idx_plot, lymph in enumerate(lymphs_plot):
            color = (1, 1, 1)
            if color_by is not None:
                if getattr(lymph, color_by) is not None:
                    color = (1-(getattr(lymph, color_by)-vmin)/(vmax-vmin), 1, 1)
            plotter.subplot(idx_plot//num_cols, idx_plot%num_cols)
            lymph.plotRecon_singleDeg(plotter, max_l = max_l, color = color)
        plotter.show(cpos=[0, 1, 0])

    def plot_l_truncations(self, idx_cell):
        plotter = pv.Plotter(shape=(2, 4), border=False)
        for idx, l in enumerate([1, 2, 3, 4, 6, 9, 12, 15]):
            plotter.subplot(idx // 4, idx %4)
            self.cells[idx_cell][0].plotRecon_singleDeg(plotter=plotter, max_l = l, uropod_align = False)
            print('l', l)
        plotter.show()