import data_loader
import region_service
from config import AppConfig

class DataAdapter:
    """数据中心适配器：负责一切数据的输入、清洗与标准化转换"""

    ENCODINGS = ['utf-8-sig', 'gbk', 'utf-8', 'gb18030']

    @staticmethod
    def read_csv_auto(file_path):
        return data_loader.read_csv_auto(file_path)
    
    @staticmethod
    def load_csv_data(file_path):
        """兼容旧调用：读取市场热力数据。"""
        return data_loader.load_csv_data(file_path)

    @staticmethod
    def load_market_data(file_path, config=AppConfig):
        """读取热力图色块数据，只使用城市和市场容量。"""
        return data_loader.load_market_data(file_path, config)

    @staticmethod
    def load_troop_data(file_path, config=AppConfig):
        """读取圆点和气泡数据，只使用城市、销量、市占率、人数。"""
        return data_loader.load_troop_data(file_path, config)

    @staticmethod
    def load_salesperson_data(file_path, config=AppConfig):
        """读取销售员标记点数据，用于兵力部署地图。"""
        return data_loader.load_salesperson_data(file_path, config)

    @staticmethod
    def filter_salespersons_by_region(records, region):
        """按营部筛选销售员兵力部署点。全国入口展示全部。"""
        return region_service.filter_salespersons_by_region(records, region)

    @staticmethod
    def export_salesperson_data(records, output_path):
        """导出兵力部署地图使用的销售员数据。"""
        return region_service.export_salesperson_data(records, output_path)

    @staticmethod
    def merge_market_and_troop_data(market_records, troop_records):
        """把热力色块数据和圆点数据按城市合并。"""
        return region_service.merge_market_and_troop_data(market_records, troop_records)

    @staticmethod
    def resolve_region_mapping_path(config):
        """兼容 Windows 隐藏扩展名导致的 .csv.csv 文件名。"""
        return region_service.resolve_region_mapping_path(config)

    @staticmethod
    def load_region_mappings(file_path, config=AppConfig):
        """
        读取全国二级营销区划分表。
        必需列：营部、城市；二级列优先用“连队”，否则使用中间那列。
        """
        return data_loader.load_region_mappings(file_path, config)

    @staticmethod
    def build_regions_from_mappings(mappings, config=AppConfig):
        """按“营部”自动生成一级营销区地图配置。"""
        return region_service.build_regions_from_mappings(mappings, config)

    @staticmethod
    def filter_by_region(records, region):
        """按营销区城市清单过滤；cities 为空时代表全国。"""
        return region_service.filter_by_region(records, region)

    @staticmethod
    def is_point_in_region(record):
        """跨区城市只在兵力数据归属与当前区域匹配时显示圆点。"""
        return region_service.is_point_in_region(record)

    @staticmethod
    def clear_point_data(record):
        """保留热力色块，清掉不属于当前区域的圆点和气泡信息。"""
        return region_service.clear_point_data(record)

    @staticmethod
    def export_region_data(records, output_path):
        """导出某张地图实际使用的数据，便于单独发送时核对。"""
        return region_service.export_region_data(records, output_path)

    @staticmethod
    def safe_filename(value):
        """清理 Windows 文件名不允许的字符。"""
        return region_service.safe_filename(value)

    @staticmethod
    def align_echarts_city_name(city_name):
        """标准地图名称过滤器 (直辖市去'市'，普通市保留)"""
        return data_loader.align_echarts_city_name(city_name)

    @staticmethod
    def city_match_key(city_name):
        """用于跨表匹配城市，兼容“成都/成都市”这类写法差异。"""
        return data_loader.city_match_key(city_name)
