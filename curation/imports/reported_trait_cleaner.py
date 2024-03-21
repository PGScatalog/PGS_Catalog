import csv
from collections import OrderedDict
from datetime import date


class ReportedTraitCleaner:
    """Class handling the cleaning of reported traits in imported studies."""

    def __init__(self, reported_traits_replacement_file: str):
        """
        Constructor. Requires the path to the file containing the mapping between known reported traits and their cleaned version.
        The file must be tab-delimited with the required columns 'trait_reported' and 'corrected'. Optional column: 'date_added'.
        """
        self.reported_traits_replacement_file = reported_traits_replacement_file
        try:
            with open(reported_traits_replacement_file, mode='r') as infile:
                reader = csv.DictReader(infile, delimiter='\t')
                self.reported_traits_dict = OrderedDict()
                for row in reader:
                    trait_reported = row['trait_reported']
                    trait_corrected = row['corrected']
                    date_added = row['date_added'] if 'date_added' in row else ''
                    self.add_trait(submitted_trait=trait_reported, corrected_trait=trait_corrected, date_added=date_added)
        except FileNotFoundError as e:
            print('ERROR: Could not find \'reported_traits_dict_file\'')
            raise e

    def clean_trait(self, submitted_trait: str) -> str:
        """
        Returns the cleaned version of the submitted trait if it exists and is defined, otherwise the submitted trait is
        returned unchanged and is added to the cleaner database.
        """
        if not self.__is_known_trait(submitted_trait):
            print('New reported trait "{}"'.format(submitted_trait))
            self.add_trait(submitted_trait=submitted_trait, corrected_trait='', date_added=str(date.today()), is_new=True)

        corrected_trait = self.__get_corrected_trait(submitted_trait)
        return corrected_trait if corrected_trait else submitted_trait

    def add_trait(self, submitted_trait: str, corrected_trait: str = '', date_added: str = '', is_new: bool = False) -> None:
        """
        Adds the given submitted trait to the cleaner database and their corrected version if exists.
        """
        self.reported_traits_dict[submitted_trait] = dict()
        self.reported_traits_dict[submitted_trait]['corrected'] = corrected_trait
        self.reported_traits_dict[submitted_trait]['date_added'] = date_added
        self.reported_traits_dict[submitted_trait]['is_new'] = is_new

    def __get_corrected_trait(self, submitted_trait: str) -> str:
        return self.reported_traits_dict[submitted_trait]['corrected']

    def __is_known_trait(self, submitted_trait: str) -> bool:
        return submitted_trait in self.reported_traits_dict

    def export(self, exported_file: str):
        """
        Save the content of the cleaner database, including the added new traits, to a new file (tab-separated) which can be used for future imports.
        """
        new_traits = []
        with open(exported_file, mode='w') as outfile:
            writer = csv.writer(outfile, delimiter='\t',
                                lineterminator='\n',
                                quotechar='"',
                                quoting=csv.QUOTE_ALL
                                )
            writer.writerow(['trait_reported', 'corrected', 'date_added'])
            for trait_reported in self.reported_traits_dict:
                corrected = self.reported_traits_dict[trait_reported]['corrected']
                date_added = self.reported_traits_dict[trait_reported]['date_added']
                writer.writerow([trait_reported, corrected, date_added])
                if self.reported_traits_dict[trait_reported]['is_new']:
                    new_traits.append(trait_reported)
            print('Updated reported trait cleaner saved to "{}"'.format(exported_file))
            print('New traits: {}'.format(str(new_traits)))

    def __contains__(self, item):
        return self.__is_known_trait(item)
