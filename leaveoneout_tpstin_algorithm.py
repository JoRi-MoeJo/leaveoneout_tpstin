# -*- coding: utf-8 -*-

"""
/***************************************************************************
 InterpolationValidation
                                 A QGIS plugin
 leave one out validation for the interpolation method thinplatespline (tin) from the SAGA console
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-05-23
        copyright            : (C) 2021 by Johannes Ritter
        email                : johannes.ritter95@web.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Johannes Ritter'
__date__ = '2021-05-23'
__copyright__ = '(C) 2021 by Johannes Ritter'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBolean,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingUtils,
                       QgsRasterLayer,
                       QgsPointXY)

import processing


class InterpolationValidationAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    SHAPES = "SHAPES"
    FIELD = "FIELD"
    TARGET = "TARGET"
    REGULARISATION = "REGULARISATION"
    LEVEL = "LEVEL"
    FRAME = "FRAME"
    OUTPUT_EXTENT = "OUTPUT_EXTENT"
    TARGET_USER_SIZE = "TARGET_USER_SIZE"
    TARGET_USER_FITS = "TARGET_USER_FITS"
    TARGET_OUT_GRID = "TARGET_OUT_GRID"
    INTERPOLATION_RESULT = "INTERPOLATION_RESULT"
    OUTPUT_DATA = "OUTPUT_DATA"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SHAPES,
                self.tr('Input vector point layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD,
                self.tr('Field to interpolate'),
                "",
                self.SHAPES
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.REGULARISATION,
                self.tr("Regularisation of interpolation"),
                QgsProcessingParameterNumber.Double,
                defaultValue=0.0001,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.LEVEL,
                self.tr("Decide for your level of Neighourhood"),
                options=[
                    self.tr("[0] immediate"),
                    self.tr("[1] Level 1"),
                    self.tr("[2] Level 2")
                ],
                defaultValue=2,
            )
        )

        self.addParameter(
            QgsProcessingParameterBolean(
                self.FRAME,
                self.tr("Frame"),
                defaultValue=1,
            )
        )

        self.addParameter(
            QgsProcessingParameterExtent(
                self.OUTPUT_EXTENT,
                self.tr("define the output extent"),
                optional=1,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TARGET_USER_SIZE,
                self.tr("Cellsize"),
                QgsProcessingParameterNumber.Double,
                defalutValue=100,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.TARGET_USER_FITS,
                self.tr("Fit - where to fit the interpolation to"),
                options=[
                    self.tr("[0] noder"),
                    self.tr("[1] cells")
                ],
                defaultValue=0
            )
        )

        # add outputs for interpolated raster and validation data
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.INTERPOLATION_RESULT,
                self.tr("Interpolation raster output layer, actively change/chosse the output. Take care that a permanent file must be an .sdat file becuase of the saga module"),
                'sdat files (*.sdat)'
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_DATA,
                self.tr("Output for validation data as .txt file"),
                'txt file (*.txt)'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        val_txt = self.parameterAsFileOutput(parameters, self.OUTPUT_DATA, context)
        parameters['TARGET_OUT_GRID'] = parameters['INTERPOLATION_RESULT']
        int_raster = processing.run(
            "saga:thinplatesplinetin",
            parameters,
            context=context,
            feedback=feedback
        )
        int_result = int_raster['TARGET_OUT_GRID']

        point_input = self.parameterAsLayer(parameters, self.SHAPES, context)
        int_field = self.parameterAsString(parameters, self.FIELD, context)
        regularisation = self.parameterAsDouble(parameters, self.REGULARISATION, context)
        neighbourhood = self.parametersAsEnum(parameters, self.LEVEL, context)
        if neighbourhood == 0:
            neighbourhood = 'immediate'
        elif neighbourhood == 1:
            neighbourhood = 'Level 1'
        elif neighbourhood == 2:
            neighbourhood = 'Level 2'
        frame = self.parameterAsBool(parameters, self.FRAME, context)
        extent = self.parameterAsExtent(parameters, self.OUTPUT_EXTENT, context)
        cellsize = self.parameterAsDouble(parameters, self.TARGET_USER_SIZE, context)
        fit = self.parameterAsEnum(parameters, self.TARGET_USER_FITS, context)
        if fit == 0:
            fit = 'nodes'
        elif fit == 1:
            fit = 'cells'
        data_out = self.paramterAsString(parameters, self.OUTPUT_DATA, context)

        fieldnames = [field.names() for field in point_input.fields()]

        gen_info = (
            'Input Layer: {}'.format(point_input.name()),
            str(point_input.crs()),
            'Interpolation field: {}'.format(int_field),
            'Features in input layer: {}'.format(point_input.feateCount())
        )
        int_info = (
            'Interpolation method: SAGA Thin plate spline (tin)',
            'Interpolation result path: {}'.format(int_result)
        )
        int_params = (
            'Regularisation: {}'.format(regularisation),
            'Neighbourhood: {}'.format(neighbourhood),
            'Frame: {}'.format(frame),
            'Output extent (xmin, ymin : xmax, ymax): {}'.format(extent.toString()),
            'Cellsize: {}'.format(cellsize),
            'Interpolation is fit to: {}'.format(fit)
        )
        header = (
            fieldnames[0],
            'x_coord',
            'y_coord',
            int_field,
            'leave one out grid value',
            'd_Poi_Interpolation'
        )

        with open(val_txt, 'w') as output_txt:
            line = ';'.join(int_info) + '\n'
            output_txt.write(line)
            line2 = ';'.join(gen_info) + '\n'
            output_txt.write(line2)
            line3 = ';'.join(int_params) + '\n'
            output_txt.write(line3)
            line4 = ';'.join(header) + '\n'
            output_txt.write(line4)
        
        parameters['TARGET_OUT_GRID'] = QgsProcessing.TEMPORARY_OUTPUT

        features = point_input.getFeatures()
        total = 100.0/point_input.featureCount() if point_input.featureCount() else 0

        for current, feat in enumerate(features):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))

            point_input.select(feat.id())
            point_input.invertSelection()
            tempfile = QgsProcessingUtils.generateTempFilename(str(feat.id())) + '.shp'
            print(tempfile)
            poi_clone = processing.run(
                "native:saveselectedfeatures", {
                    'INPUT': point_input,
                    'OUPUT': tempfile
                }, 
                context=context,
                feedback=feedback
            )['OUTPUT']
            parameters['SHAPES'] = poi_clone
            val_int = processing.run(
                "saga:thinplatesplinetin",
                parameters,
                context=context,
                feedback=feedback
            )
            print(val_int['TARGET_OUT_GRID'])
            valraster = QgsRasterLayer(
                val_int['TARGET_OUT_GRID'],
                'valint_raster',
                'gdal'
            )
            point_input.removeSelection()

            poi_value = feat.attribute(str(int_field))
            geom = feat.geometry()
            valraster_value, res = valraster.dataProvider().sample(
                QgsPointXY(geom.asPoint().x(), geom.asPoint().y()),
                1
            )
            if res == False:
                delta = 'NaN'
            elif res == True:
                delta = poi_value - valraster_value
            else:
                print('something went horribly wrong here :(')
            
            txtdata = (
                str(feat.attribute(0)),
                '{:.4f}'.format(geom.asPoint().x()),
                '{:.4f}'.format(geom.asPoint().y()),
                str(feat.attribute(int_field)),
                str(valraster_value),
                str(delta)
            )
            with open(val_txt, 'a') as output_txt:
                data = ';'.join(txtdata) + '\n'
                output_txt.write(data)
            

        return {
            self.INTERPOLATION_RESULT: int_result,
            self.OUTPUT_DATA: val_txt
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'leave one out validation TPS (tin)'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'interpolation validation'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return InterpolationValidationAlgorithm()
