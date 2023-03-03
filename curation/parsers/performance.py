import re
from psycopg2.extras import NumericRange
from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from curation.parsers.metric import MetricData
from catalog.models import Performance

class PerformanceData(GenericData):

    def __init__(self,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.metrics = []
        self.metric_models = []


    def add_metric(self, field, val):
        '''
        Method encapsulating the method str2metric and add the returned MetricData object to the metrics array.
        - field: data field (from the template schema)
        - val: data value
        '''
        metric = self.str2metric(field, val)
        if metric:
            self.metrics.append(metric)


    def str2metric(self, field, val):
        '''
        Parse the metric information to store it into the MetricData object
        - field: data field (from the template schema)
        - val: data value
        Return type: MetricData object
        '''
        _, ftype, fname = field.split('_')

        #print(f'ftype: {ftype} | fname: {fname} | _: {_}')

        current_metric = MetricData(ftype,fname,val,self.spreadsheet_name)
        current_metric.set_names()
        val = current_metric.value

        # Parse out the confidence interval and estimate

        ## Simple float or int value
        if type(val) == float or type(val) == int:
            current_metric.add_data('estimate', val)
            return current_metric

        ## Other values with interval, parenthesis, units ...
        val = val.strip()

        # Check if SE is reported (parenthesis)
        matches_parentheses = self.inparentheses.findall(val)
        if len(matches_parentheses) == 1:
            val = val.split('(')[0].strip()
            # Check extra character/data after the parenthesis
            extra = val.strip().split(')')
            if len(extra) > 1:
                self.parsing_report_error(f'Extra information detected after the parenthesis for: {val}')
            try:
                current_metric.add_data('estimate', float(val))
            except:
                val, unit = val.split(" ", 1)
                current_metric.add_data('estimate', float(val))
                current_metric.add_data('unit', unit)
            current_metric.add_data('se', matches_parentheses[0])
        # Extract interval
        elif '[' in str(val) and ']' in str(val):
            try:
                estimate = float(val.split(' [')[0])
                current_metric.add_data('estimate', estimate)
                # Check extra character/data after the brackets
                extra = val.strip().split(']')
                if len(extra) > 1:
                    # Check if second part has content
                    if (extra[1] != ''):
                        self.parsing_report_error(f'Extra information detected after the interval for: "{val}"')
            except Exception as e:
                self.parsing_report_error(f'Can\'t extract the estimate value from ({val}): {e}')
                current_metric.add_data('estimate', val)
                return

            matches_square = self.insquarebrackets.findall(val)
            if len(matches_square) == 1:
                bracket_value = matches_square[0]
                # Harmonise by transforming the long dash in normal dash
                if '–' in bracket_value:
                    bracket_value = bracket_value.replace('–','-')

                if re.search(self.interval_format,bracket_value):
                    ci_match = tuple(map(float, bracket_value.split(' - ')))
                    current_metric.add_data('ci', NumericRange(lower=ci_match[0], upper=ci_match[1], bounds='[]'))
                    min_ci = float(ci_match[0])
                    max_ci = float(ci_match[1])
                    estimate = float(current_metric.data['estimate'])
                    # Check that the estimate is within the interval
                    if not min_ci <= estimate <= max_ci:
                        self.parsing_report_error(f'The estimate value ({estimate}) is not within its the confidence interval [{min_ci} - {max_ci}]')
                else:
                    self.parsing_report_error(f'Confidence interval "{val}" is not in the expected format (e.g. "1.00 [0.80 - 1.20]")')
        # Extact unit
        else:
            try:
                current_metric.add_data('estimate', float(val))
            except:
                val, unit = val.split(" ", 1)
                current_metric.add_data('estimate', float(val))
                current_metric.add_data('unit', unit)

        return current_metric


    @transaction.atomic
    def create_performance_model(self, publication, score, sampleset):
        '''
        Create an instance of the Performance model.
        - publication: instance of the Publication model
        - score: instance of the Score model
        - sampleset: instance of the SampleSet model
        Return type: Performance model
        '''
        try:
            with transaction.atomic():
                self.model = Performance(publication=publication, score=score, sampleset=sampleset)
                self.model.set_performance_id(self.next_id_number(Performance))
                for field, val in self.data.items():
                    if field not in ['publication','score','sampleset']:
                        setattr(self.model, field, val)
                self.model.save()

            # Create associated Metric objects
            for metric in self.metrics:
                metric_model = metric.create_metric_model(self.model)
                self.metric_models.append(metric_model)

        except IntegrityError as e:
            self.model = None
            self.parsing_report_error_import(e)
            print('Error with the creation of the Performance(s) and/or the Metric(s)')

        return self.model
