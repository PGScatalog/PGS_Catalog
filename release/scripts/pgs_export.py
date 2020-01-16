import sys, os.path, tarfile
import pandas as pd
import hashlib
from catalog.models import *

class PGSExport:

    #---------------#
    # Configuration #
    #---------------#

    fields_to_include = {
        'EFOTrait':
            [[
                'id',
                'label',
                'description',
                'url'
            ]],
        'Sample':
            [
                [
                    'sample_number',
                    'sample_cases',
                    'sample_controls',
                    'sample_percent_male',
                    'sample_age',
                    'phenotyping_free',
                    'ancestry_broad',
                    'ancestry_free',
                    'source_GWAS_catalog',
                    'source_PMID',
                    'cohorts_list'
                ],
                [
                    'sample_number',
                    'sample_cases',
                    'sample_controls',
                    'sample_percent_male',
                    'sample_age',
                    'phenotyping_free',
                    'ancestry_broad',
                    'ancestry_free',
                    'associated_scores',
                    'source_GWAS_catalog',
                    'source_PMID',
                    'cohorts_list'
                ]
            ],
        'SampleSet':
            [[
                'id'
            ]],
        'Score':
            [[
                'id',
                'name',
                'trait_reported',
                'method_name',
                'method_params',
                'trait_label',
                'trait_id',
                'pub_pmid_label',
                'pub_doi_label',
                'variants_number',
                'variants_genomebuild'
            ]],
        'Performance':
            [[
                'id',
                'score',
                'sampleset',
                'pheotyping_reported',
                'pub_pmid_label',
                'pub_doi_label',
                'covariates',
                'performance_comments'
            ]],
            'Publication':
                [[
                    'id',
                    'doi',
                    'PMID',
                    'journal',
                    'firstauthor',
                    'authors',
                    'title',
                    'date_publication'
                ]]
    }

    extra_fields_to_include = {
        'trait_label': 'Mapped Trait(s) (EFO label)',
        'trait_id'   : 'Mapped Trait(s) (EFO ID)',
        'pub_pmid_label' : 'Publication (PMID)',
        'pub_doi_label'  : 'Publication (doi)',
        'cohorts_list' : 'Cohort(s)',
        'associated_scores' : 'Associated scores'
    }

    # Metrics
    other_metric_key = 'Other Metric'
    other_metric_label = other_metric_key+'(s)'
    metrics_type = ['HR','OR','β','AUROC','C-index',other_metric_label]
    metrics_header = {
        'HR': 'Hazard Ratio (HR)',
        'OR': 'Odds Ratio (OR)',
        'β': 'Beta',
        'AUROC': 'Area Under the Receiver-Operating Characteristic Curve (AUROC)',
        'C-index': 'Corcordance Statistic (C-index)',
        other_metric_key: other_metric_label
    }

    def __init__(self,filename):
        self.filename = filename
        self.writer   = pd.ExcelWriter(filename, engine='xlsxwriter')

    def save(self):
        """ Close the Pandas Excel writer and output the Excel file """
        self.writer.save()


    def generate_sheet(self, data, sheet_name):
        """ Generate the Pandas dataframe and insert it as a spreadsheet into to the Excel file """
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Convert the dataframe to an XlsxWriter Excel object.
            df.to_excel(self.writer, index=False, sheet_name=sheet_name)
        except NameError:
            print("Spreadsheet generation: At least one of the variables is not defined")
        except:
            print("Spreadsheet generation: There is an issue with the data of the spreadsheet '"+str(sheet_name)+"'")


    def generate_csv(self, data, prefix, sheet_name):
        """ Generate the Pandas dataframe and create a CSV file """
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Convert the dataframe to an XlsxWriter Excel object.
            sheet_name = sheet_name.lower().replace(' ', '_')
            csv_filename = prefix+"_metadata_"+sheet_name+".csv"
            df.to_csv(csv_filename, index=False)
        except NameError:
            print("CSV generation: At least one of the variables is not defined")
        except:
            print("CSV generation: There is an issue with the data of the type '"+str(sheet_name)+"'")


    def generate_tarfile(self, output_filename, source_dir):
        """ Generate a tar.gz file from a directory """
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))


    def get_column_labels(self, classname, index=0, exception_field=None, exception_classname=None):
        """ Fetch the column labels from the Models """
        model_fields = [f.name for f in classname._meta.fields]
        model_labels = {}

        classname_string = classname.__name__

        for field_name in self.fields_to_include[classname_string][index]:
            label = None
            if field_name in model_fields:
                label = classname._meta.get_field(field_name).verbose_name
            elif exception_field and field_name in exception_field:
                exception_field_name = 'id'
                label = exception_classname._meta.get_field(exception_field_name).verbose_name
            elif field_name in self.extra_fields_to_include:
                label = self.extra_fields_to_include[field_name]
            else:
                print("Error: the field '"+field_name+"' can't be found for the class "+classname_string)

            if label:
                model_labels[field_name] = label
        return model_labels


    def not_in_extra_fields_to_include(self,column):
        if column not in self.extra_fields_to_include.keys():
            return True
        else:
            return False


    def create_md5_checksum(self, md5_filename='md5_checksum.txt', blocksize=4096):
        """ Returns MD5 checksum for the generated file. """

        md5 = hashlib.md5()
        try:
            file = open(self.filename, 'rb')
            with file:
                for block in iter(lambda: file.read(blocksize), b""):
                    md5.update(block)
        except IOError:
            print('File \'' + self.filename + '\' not found!')
            return None
        except:
            print("Error: the script couldn't generate a MD5 checksum for '" + self.filename + "'!")
            return None

        md5file = open(md5_filename, 'w')
        md5file.write(md5.hexdigest())
        md5file.close()
        print("MD5 checksum file '"+md5_filename+"' has been generated.")


    #---------------------#
    # Spreadsheet methods #
    #---------------------#

    def create_scores_spreadsheet(self, pgs_list=[]):
        """ Score spreadsheet """

        # Fetch column labels an initialise data dictionary
        score_labels = self.get_column_labels(Score)
        scores_data = {}
        for label in list(score_labels.values()):
            scores_data[label] = []

        scores = []
        if len(pgs_list) == 0:
            scores = Score.objects.all()
        else:
            scores = Score.objects.filter(id__in=pgs_list)


        for score in scores:
            # Publication
            scores_data[score_labels['pub_pmid_label']].append(score.publication.PMID)
            scores_data[score_labels['pub_doi_label']].append(score.publication.doi)
            # Mapped Traits
            trait_labels = []
            trait_ids = []
            for trait in score.trait_efo.all():
                trait_labels.append(trait.label)
                trait_ids.append(trait.id)
            scores_data[score_labels['trait_label']].append(', '.join(trait_labels))
            scores_data[score_labels['trait_id']].append(', '.join(trait_ids))

            # Load the data into the dictionnary
            # e.g. column is "id":
            # `getattr` generates the perf.score method call
            # The following code is actually run:
            # scores_data[score_labels['id']].append(score.id)
            for column in score_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(score, column)
                    scores_data[score_labels[column]].append(object_method_name)

        return scores_data


    def create_performance_metrics_spreadsheet(self, pgs_list=[]):
        """ Performance Metrics spreadsheet """

        metrics_header = self.metrics_header
        metrics_type = self.metrics_type
        other_metric_label = self.other_metric_label

        # Fetch column labels an initialise data dictionary
        score_field = 'score'
        perf_labels = self.get_column_labels(Performance, exception_field=score_field, exception_classname=Score)
        perf_data = {}
        for label in list(perf_labels.values()):
            perf_data[label] = []

        # Addtional fields

        # Metrics
        for m_header in metrics_header:
            full_header = metrics_header[m_header]
            perf_data[full_header]  = []


        performances = []
        if len(pgs_list) == 0:
            performances = Performance.objects.all()
        else:
            for pgs_id in pgs_list:
                score = Score.objects.get(id__exact=pgs_id)
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    if score_perf not in performances:
                        performances.append(score_perf)

        for perf in performances:
            # Publication
            perf_data[perf_labels['pub_pmid_label']].append(perf.publication.PMID)
            perf_data[perf_labels['pub_doi_label']].append(perf.publication.doi)

            # Metrics
            metrics_data = {}
            for m_header in list(metrics_header.values()):
                metrics_data[m_header] = ""
            # Effect sizes
            effect_sizes_list = perf.effect_sizes_list
            if effect_sizes_list:
                for metric in effect_sizes_list:
                    #print(metric[0]+": "+str(metric[1]))
                    if metric[0][1] in metrics_type:
                        m_header = metrics_header[metric[0][1]]
                        metrics_data[m_header] = metric[1]
            # Classification metrics
            class_acc_list = perf.class_acc_list
            if class_acc_list:
                for metric in class_acc_list:
                    if metric[0][1] in metrics_type:
                        m_header = metrics_header[metric[0][1]]
                        metrics_data[m_header] = metric[1]
            # Other metrics
            othermetrics_list = perf.othermetrics_list
            if othermetrics_list:
                for metric in othermetrics_list:
                    m_data = metric[0][1]+": "+metric[1]
                    if metrics_data[other_metric_label] == '':
                        metrics_data[other_metric_label] = m_data
                    else:
                        metrics_data[other_metric_label] = metrics_data[other_metric_label]+", "+m_data

            for m_header in list(metrics_header.values()):
                perf_data[m_header].append(metrics_data[m_header])

            # Load the data into the dictionnary
            # e.g. column is "score":
            # `getattr` generates the perf.score method call
            # The following code is actually run:
            # perf_data[perf_labels['score']].append(perf.score)
            for column in perf_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    # Exception for the score entry
                    if column == score_field:
                        object_method_name = perf.score.id
                    else:
                        object_method_name = getattr(perf, column)

                    perf_data[perf_labels[column]].append(object_method_name)

        return perf_data


    def create_samplesets_spreadsheet(self, pgs_list=[]):
        """ Sample Sets spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(SampleSet)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        # Sample
        sample_object_labels = self.get_column_labels(Sample)
        for label in list(sample_object_labels.values()):
            object_data[label] = []

        samplesets = []
        if len(pgs_list) == 0:
            samplesets = SampleSet.objects.all()
        else:
            for pgs_id in pgs_list:
                score = Score.objects.get(id__exact=pgs_id)
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    sampleset = SampleSet.objects.get(id__exact=score_perf.sampleset)
                    if sampleset not in samplesets:
                        samplesets.append(sampleset)

        for pss in samplesets:
            for sample in pss.samples.all():
                object_data[sample_object_labels['cohorts_list']].append(', '.join([c.name_short for c in sample.cohorts.all()]))

                for sample_column in sample_object_labels.keys():
                    if self.not_in_extra_fields_to_include(sample_column):
                        sample_object_method_name = getattr(sample, sample_column)
                        object_data[sample_object_labels[sample_column]].append(sample_object_method_name)

                for column in object_labels.keys():
                    if self.not_in_extra_fields_to_include(column):
                        object_method_name = getattr(pss, column)
                        object_data[object_labels[column]].append(object_method_name)

        return object_data


    def create_sample_training_spreadsheet(self, pgs_list=[]):
        """ Sample training spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(Sample,index=1)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        samples = []
        if len(pgs_list) == 0:
            samples = Sample.objects.all()
        else:
            scores = Score.objects.filter(id__in=pgs_list)
            for score in scores:
                for score_sample in score.samples_training.all():
                    samples.append(score_sample)

        for sample in samples:

            scores = Score.objects.filter(samples_training__id=sample.id)
            if len(scores) == 0:
                continue

            object_data[object_labels['associated_scores']].append(', '.join([s.id for s in scores]))

            object_data[object_labels['cohorts_list']].append(', '.join([c.name_short for c in sample.cohorts.all()]))

            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(sample, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data


    def create_sample_variants_spreadsheet(self, pgs_list=[]):
        """ Source of Variant Associations spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(Sample,index=1)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        samples = []
        if len(pgs_list) == 0:
            samples = Sample.objects.all()
        else:
            scores = Score.objects.filter(id__in=pgs_list)
            for score in scores:
                for score_sample in score.samples_variants.all():
                    samples.append(score_sample)

        for sample in samples:

            scores = Score.objects.filter(samples_variants__id=sample.id)
            if len(scores) == 0:
                continue

            object_data[object_labels['associated_scores']].append(', '.join([s.id for s in scores]))

            object_data[object_labels['cohorts_list']].append(', '.join([c.name_short for c in sample.cohorts.all()]))

            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(sample, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data


    def create_publications_spreadsheet(self, pgs_list=[]):
        """ Publications spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(Publication)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        publications = []
        if len(pgs_list) == 0:
            publications = Publication.objects.all()
        else:
            scores = Score.objects.filter(id__in=pgs_list)
            for score in scores:
                # Score publication
                score_publication = score.publication
                if score_publication not in publications:
                    publications.append(score_publication)

                # Performance publication
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    perf_publication = score_perf.publication
                    if perf_publication not in publications:
                        publications.append(perf_publication)

        for publi in publications:

            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(publi, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data


    def create_efo_traits_spreadsheet(self, pgs_list=[]):
        """ EFO traits spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(EFOTrait)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        traits = []
        if len(pgs_list) == 0:
            traits = EFOTrait.objects.all()
        else:
            scores = Score.objects.filter(id__in=pgs_list)
            for score in scores:
                score_traits = score.trait_efo
                for score_trait in score_traits.all():
                    if score_trait not in traits:
                        traits.append(score_trait)

        for trait in traits:

            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(trait, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data
